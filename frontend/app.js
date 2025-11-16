const { useState, useEffect } = React;

const API_URL = 'http://localhost:8000/api/v1/tasks/';

function App() {
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        async function fetchTasks() {
            try {
                // Assuming the API requires authentication, using a placeholder token.
                // In a real app, this would come from a login process.
                const FAKE_TOKEN = 'your_jwt_token_here';

                const response = await fetch(API_URL, {
                    headers: {
                        'Authorization': `Bearer ${FAKE_TOKEN}`
                    }
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                setTasks(data);
            } catch (e) {
                setError(e.message);
            } finally {
                setLoading(false);
            }
        }

        fetchTasks();
    }, []);

    const getStatusClass = (status) => {
        if (status === 'done') return 'status-done';
        if (status === 'doing') return 'status-doing';
        return 'status-todo';
    };

    const renderPlugins = () => {
        if (!window.TaskForgePlugins) return null;
        return window.TaskForgePlugins.map(plugin => {
            const PluginComponent = plugin.component;
            return <PluginComponent key={plugin.id} tasks={tasks} />;
        });
    };

    if (loading) return <div>Loading tasks...</div>;
    if (error) return <div>Error fetching tasks: {error}</div>;

    return (
        <div>
            <h1>My Tasks</h1>
            {tasks.length > 0 ? (
                tasks.map(task => (
                    <div key={task.id} className="task-item">
                        <span className={`task-status ${getStatusClass(task.status)}`}>{task.status}</span>
                        <div className="task-title">{task.title}</div>
                        <p>{task.description}</p>
                    </div>
                ))
            ) : (
                <p>No tasks found. Please run the API and ensure you have tasks.</p>
            )}
            <hr />
            <div className="plugin-area">{renderPlugins()}</div>
        </div>
    );
}

const container = document.getElementById('root');
const root = ReactDOM.createRoot(container);
root.render(<App />);
