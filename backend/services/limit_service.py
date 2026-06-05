from config.limits import (
    MAX_EPOCHS,
    MAX_BATCH_SIZE,
    MAX_NUM_WORKERS,
    MAX_SEGMENT_DURATION,
)

def get_current_limits():
    return {
        "max_segment_duration": MAX_SEGMENT_DURATION,
        "max_epochs": MAX_EPOCHS,
        "max_batch_size": MAX_BATCH_SIZE,
        "max_num_workers": MAX_NUM_WORKERS,
    }