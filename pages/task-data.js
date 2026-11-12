(() => {
  const storageKey = "cogniplan.tasks";
  const statuses = ["Draft", "In Progress", "Editing", "Done"];
  const priorities = ["LOW", "MEDIUM", "HIGH", "URGENT"];
  const seedTasks = [
    { id: "task-1", title: "Develop Node.js Route Handlers (PCM Mock)", category: "PCM Backend", priority: "HIGH", status: "Draft" },
    { id: "task-2", title: "Develop Node.js Route Handlers (PCM Mock)", category: "PCM Backend", priority: "MEDIUM", status: "Draft" },
    { id: "task-3", title: "Write MySQL Schema Migration Script", category: "SQL Arch", priority: "MEDIUM", status: "In Progress" },
    { id: "task-4", title: "Write MySQL Schema Migration Script", category: "Node Engine", priority: "HIGH", status: "In Progress" },
    { id: "task-5", title: "Implement Real-Time Update Logic (WebSocket)", category: "Node Engine", priority: "HIGH", status: "In Progress" },
    { id: "task-6", title: "Implement Real-Time Update Logic (WebSocket)", category: "Node Engine", priority: "HIGH", status: "Editing" },
    { id: "task-7", title: "Implement Real-Time Update Logic (WebSocket)", category: "Node Engine", priority: "MEDIUM", status: "Editing" },
    { id: "task-8", title: "Refactor Express Middleware for Auth", category: "Node Engine", priority: "HIGH", status: "Done" },
    { id: "task-9", title: "Refactor Express Middleware for Auth", category: "Node Engine", priority: "MEDIUM", status: "Done" }
  ];

  function reportStorageError(message, error) {
    console.error(message, error);
    window.AppUI.toast(message, "error");
  }

  function normalizePriority(priority) {
    const value = String(priority || "").trim().toUpperCase();
    const normalized = value === "MID" ? "MEDIUM" : value;
    if (!priorities.includes(normalized)) {
      throw new Error(`Unsupported task priority: ${priority}`);
    }
    return normalized;
  }

  function normalizeTask(task) {
    if (!task || typeof task.id !== "string" || !task.id || typeof task.title !== "string" || !task.title.trim()) {
      throw new Error("Saved task data contains an invalid task.");
    }
    if (!statuses.includes(task.status)) {
      throw new Error(`Unsupported task status: ${task.status}`);
    }
    return {
      id: task.id,
      title: task.title.trim(),
      description: typeof task.description === "string" ? task.description : "",
      category: typeof task.category === "string" ? task.category : "PCM Backend",
      priority: normalizePriority(task.priority),
      status: task.status,
      favorite: Boolean(task.favorite)
    };
  }

  function readTasks() {
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved === null) {
        localStorage.setItem(storageKey, JSON.stringify([]));
        return [];
      }
      const parsed = JSON.parse(saved);
      if (!Array.isArray(parsed)) throw new Error("Saved task data must be a list.");
      return parsed.map(normalizeTask);
    } catch (error) {
      reportStorageError("Task data could not be loaded from this device.", error);
      throw error;
    }
  }

  function writeTasks(tasks) {
    const normalized = tasks.map(normalizeTask);
    try {
      localStorage.setItem(storageKey, JSON.stringify(normalized));
    } catch (error) {
      reportStorageError("Task data could not be saved on this device.", error);
      throw error;
    }
    // Keep the existing synchronous UI model, while persisting the same changes to MySQL.
    if (window.CogniPlanAPI && window.CogniPlanAPI.post) {
      syncQueue = syncQueue.then(() => window.CogniPlanAPI.post("/api/tasks/sync", { tasks: normalized }))
        .catch(error => { console.error("Cloud task sync failed:", error); window.AppUI?.toast("Task saved on this device, but cloud sync failed: " + error.message, "error"); });
    }
    return normalized;
  }

  let syncQueue = Promise.resolve();

  function getAll() {
    return readTasks();
  }

  function add(task) {
    const tasks = readTasks();
    const id = `task-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const created = normalizeTask({ ...task, id });
    writeTasks([...tasks, created]);
    return created;
  }

  function update(id, changes) {
    const tasks = readTasks();
    let updated = null;
    const next = tasks.map(task => {
      if (task.id !== id) return task;
      updated = normalizeTask({ ...task, ...changes, id });
      return updated;
    });
    if (!updated) throw new Error(`Task not found: ${id}`);
    writeTasks(next);
    return updated;
  }

  function remove(id) {
    const tasks = readTasks();
    const next = tasks.filter(task => task.id !== id);
    if (next.length === tasks.length) throw new Error(`Task not found: ${id}`);
    writeTasks(next);
  }

  window.CogniPlanTasks = {
    storageKey,
    statuses,
    priorities,
    normalizePriority,
    getAll,
    add,
    update,
    remove
  };

  // Load this signed-in user's tasks from MySQL before the page's next render.
  if (window.CogniPlanAPI) {
    window.CogniPlanAPI.get("/api/tasks").then(result => {
      const remote = (result.tasks || []).map(task => normalizeTask({
        id: String(task.id), title: task.title, description: task.description || "",
        category: task.category || "Uncategorized", priority: task.priority,
        status: task.status, favorite: Boolean(task.is_starred)
      }));
      const current = (() => { try { return JSON.parse(localStorage.getItem(storageKey) || "[]"); } catch { return []; } })();
      const reloadKey = "cogniplan.tasks.hydrated." + location.pathname;
      if (JSON.stringify(current) !== JSON.stringify(remote)) {
        localStorage.setItem(storageKey, JSON.stringify(remote));
        // Existing page scripts are synchronous; reload once so they render the fetched data.
        if (!sessionStorage.getItem(reloadKey)) { sessionStorage.setItem(reloadKey, "1"); location.reload(); }
      } else {
        sessionStorage.removeItem(reloadKey);
      }
    }).catch(error => {
      if (!String(error.message).includes("401")) console.warn("Could not load cloud tasks:", error.message);
    });
  }
})();
