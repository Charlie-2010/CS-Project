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
        localStorage.setItem(storageKey, JSON.stringify(seedTasks));
        return seedTasks.map(normalizeTask);
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
    return normalized;
  }

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
})();
