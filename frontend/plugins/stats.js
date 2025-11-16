// Plugin definition
window.TaskForgePlugins = window.TaskForgePlugins || [];

window.TaskForgePlugins.push({
    name: 'Task Statistics',
    id: 'task-stats-widget',
    component: (props) => {
        const { tasks } = props;

        if (!tasks || tasks.length === 0) {
            return <div>No tasks to analyze.</div>;
        }

        const total = tasks.length;
        const done = tasks.filter(t => t.status === 'done').length;
        const doing = tasks.filter(t => t.status === 'doing').length;
        const todo = tasks.filter(t => t.status === 'todo').length;

        return (
            <div style={{ border: '1px solid #ccc', padding: '10px', marginTop: '20px', borderRadius: '4px' }}>
                <h3>📊 Task Statistics</h3>
                <p><strong>Total Tasks:</strong> {total}</p>
                <p><strong>Done:</strong> {done} ({Math.round((done/total)*100)}%)</p>
                <p><strong>In Progress:</strong> {doing}</p>
                <p><strong>To Do:</strong> {todo}</p>
            </div>
        );
    }
});
