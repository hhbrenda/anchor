const KEYS = {
    DATA: 'aac_data_v4' // Bumped version for schema change
};

const DEFAULT_DATA = {
    settings: {
        cadence: 'daily',
        theme: 'dark'
    },
    user: {
        name: 'Friend',
        goals: [], // Strings
        notes: '' // Long-term memory for AI
    },
    projects: [] // { id, title, threadId (deprecated), tasks: [], checkins: [] }
};

export const storage = {
    // --- CORE ACCESS ---
    getData: () => {
        try {
            const data = localStorage.getItem(KEYS.DATA);
            return data ? JSON.parse(data) : DEFAULT_DATA;
        } catch { return DEFAULT_DATA; }
    },
    saveData: (data) => {
        localStorage.setItem(KEYS.DATA, JSON.stringify(data));
    },

    // --- USER PROFILE ---
    getUser: () => {
        return storage.getData().user || DEFAULT_DATA.user;
    },
    updateUser: (updates) => {
        const data = storage.getData();
        data.user = { ...data.user, ...updates };
        storage.saveData(data);
    },

    // --- PROJECT MANAGEMENT ---
    getProjects: () => {
        return storage.getData().projects;
    },

    addProject: (title, description) => {
        const data = storage.getData();
        const newProject = {
            id: Date.now().toString(),
            title,
            description: description || '',
            tasks: [],
            checkins: []
        };
        data.projects.push(newProject);
        storage.saveData(data);
        return newProject;
    },

    deleteProject: (id) => {
        const data = storage.getData();
        data.projects = data.projects.filter(p => p.id !== id);
        storage.saveData(data);
    },

    updateProject: (id, updates) => {
        const data = storage.getData();
        const idx = data.projects.findIndex(p => p.id === id);
        if (idx > -1) {
            data.projects[idx] = { ...data.projects[idx], ...updates };
            storage.saveData(data);
        }
    },

    getProject: (id) => {
        const projects = storage.getData().projects;
        return projects.find(p => p.id === id);
    },

    // --- TASK MANAGEMENT (Scoped to Project) ---
    updateProjectTasks: (projectId, newTasks) => {
        const data = storage.getData();
        const projectIndex = data.projects.findIndex(p => p.id === projectId);
        if (projectIndex > -1) {
            data.projects[projectIndex].tasks = newTasks;
            storage.saveData(data);
        }
    },

    // --- SETTINGS ---
    getSettings: () => {
        return storage.getData().settings;
    },
    saveSettings: (newSettings) => {
        const data = storage.getData();
        data.settings = { ...data.settings, ...newSettings };
        storage.saveData(data);
    },

    // --- RESET ---
    clearAll: async () => {
        try {
            await fetch('http://localhost:8000/api/thread/active', { method: 'DELETE' });
        } catch (e) {
            console.error("Failed to clear server thread:", e);
        }
        localStorage.removeItem(KEYS.DATA);
        localStorage.removeItem('aac_chat_history');
        localStorage.removeItem('aac_global_thread_id');
        window.location.reload();
    },

    // --- THEME ---
    getTheme: () => {
        return storage.getSettings().theme || 'dark';
    },
    setTheme: (theme) => {
        storage.saveSettings({ theme });
        document.documentElement.setAttribute('data-theme', theme);
    },
    initTheme: () => {
        const theme = storage.getTheme();
        document.documentElement.setAttribute('data-theme', theme);
        return theme;
    }
};
