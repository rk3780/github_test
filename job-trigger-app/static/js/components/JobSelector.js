// JobSelector Component
window.JobSelector = function({ jobs, selectedJob, onJobSelect, disabled }) {
    return (
        <div className="form-group">
            <label htmlFor="job-select">Select Job</label>
            <select 
                id="job-select"
                value={selectedJob} 
                onChange={(e) => onJobSelect(e.target.value)}
                disabled={disabled}
            >
                <option value="">-- Select a job --</option>
                {jobs.map(job => (
                    <option key={job.job_id} value={job.job_id}>
                        {job.name} (ID: {job.job_id})
                    </option>
                ))}
            </select>
        </div>
    );
};