from app import create_app
from app.scheduler import init_scheduler, stop_scheduler

app = create_app()

if __name__ == '__main__':
    # Initialize the background alert scheduler
    init_scheduler(app)
    
    try:
        app.run(debug=True)
    except KeyboardInterrupt:
        print("\nShutting down...")
        stop_scheduler()
