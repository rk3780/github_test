// TriggerButton Component
window.TriggerButton = function({ onTrigger, disabled, triggering }) {
    return (
        <button 
            onClick={onTrigger} 
            disabled={disabled}
        >
            {triggering ? 'Triggering...' : 'Trigger Job'}
        </button>
    );
};