import uvicorn

from application import create_app
from routes import include_routes

# Create the FastAPI application
app = create_app()

# Include all routes
include_routes(app)

if __name__ == "__main__":
    # Example curl commands for testing:

    # Create an event:
    # curl -X POST "http://localhost:8000/events" \
    # -H "Content-Type: application/json" \
    # -d '{"title": "Project Meeting", "description": "Weekly sync", \
    #      "start_date": "2024-01-01T10:00:00", "end_date": "2024-01-01T11:00:00", \
    #      "user_id": "user-id-here", "people": ["John", "Jane"]}'
    #
    # Create a task:
    # curl -X POST "http://localhost:8000/tasks" \
    # -H "Content-Type: application/json" \
    # -d '{"title": "Setup Database", "description": "Initialize the DB", \
    #      "duration": 120, "event_id": "event-id-here", "people": ["John"], \
    #      "maintainer_id": "user-id-here"}'
    #
    # Create a story:
    # curl -X POST "http://localhost:8000/stories?user_id=user-id-here" \
    # -H "Content-Type: application/json" \
    # -d '{"title": "My First Story", \
    #      "content": "# Hello World\nThis is my story.", \
    #      "task_id": "task-id-here"}'
    #
    # Update story content:
    # curl -X PATCH \
    #      "http://localhost:8000/stories/story-id-here/content?user_id=user-id-here" \
    # -H "Content-Type: application/json" \
    # -d '{"content": "# Hello World\nThis is my updated story content."}'
    #
    # Get story revision history:
    # curl "http://localhost:8000/stories/story-id-here/revisions?user_id=user-id-here"
    #
    # Create invite:
    # curl -X POST "http://localhost:8000/invites?user_id=maintainer-id-here" \
    # -H "Content-Type: application/json" \
    # -d '{"task_id": "task-id-here", "invitee_id": "user-id-here", \
    #      "role": "collaborator", "message": "Join our task!"}'
    #
    # List received invites:
    # curl "http://localhost:8000/invites/received/user-id-here"
    #
    # Respond to invite:
    # curl -X PATCH \
    #      "http://localhost:8000/invites/invite-id-here?user_id=invitee-id-here" \
    # -H "Content-Type: application/json" \
    # -d '{"status": "accepted"}'
    #
    # List notifications:
    # curl "http://localhost:8000/notifications/user-id-here"
    #
    # Mark notification as read:
    # curl -X PATCH \
    #      "http://localhost:8000/notifications/notification-id-here?" \
    #      "user_id=user-id-here" \
    # -H "Content-Type: application/json" \
    # -d '{"is_read": true}'

    uvicorn.run(app, host="0.0.0.0", port=8000)
