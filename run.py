import os
from app import create_app
from app.scheduler import init_scheduler, stop_scheduler

app = create_app()

if __name__ == '__main__':
    init_scheduler(app)
    
    port = int(os.environ.get("PORT", 5000))
    try:
        app.run(host="0.0.0.0", port=port)
    except KeyboardInterrupt:
        print("\nShutting down...")
        stop_scheduler()
