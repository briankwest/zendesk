from flask import Flask, jsonify, send_file
import os
import requests
from dotenv import load_dotenv
from flask_httpauth import HTTPBasicAuth
from signalwire_swaig.core import SWAIG, SWAIGArgument

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Retrieve environment variables
ZENDESK_SUBDOMAIN = os.getenv('ZENDESK_SUBDOMAIN')
ZENDESK_API_TOKEN = os.getenv('ZENDESK_API_TOKEN')
ZENDESK_EMAIL = os.getenv('ZENDESK_EMAIL')
HTTP_USERNAME = os.getenv('HTTP_USERNAME')
HTTP_PASSWORD = os.getenv('HTTP_PASSWORD')

auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    if username == HTTP_USERNAME and password == HTTP_PASSWORD:
        return True
    return False

# Helper function to authenticate with Zendesk using Bearer token
from requests.auth import HTTPBasicAuth

def zendesk_auth():
    return HTTPBasicAuth(f"{ZENDESK_EMAIL}/token", ZENDESK_API_TOKEN)

def format_ticket_info(ticket_info):
    if not ticket_info:
        return "No ticket information available."

    formatted_info = (
        f"Ticket ID: {ticket_info.get('id')}\n"
        f"Subject: {ticket_info.get('subject')}\n"
        f"Status: {ticket_info.get('status')}\n"
        f"Priority: {ticket_info.get('priority')}\n"
        f"Requester: {ticket_info.get('requester', {}).get('name')}\n"
        f"Created At: {ticket_info.get('created_at')}\n"
        f"Updated At: {ticket_info.get('updated_at')}\n"
        f"Description: {ticket_info.get('description')}\n"
    )
    return formatted_info

# Initialize SWAIG with the Flask app and authentication
swaig = SWAIG(app, auth=(HTTP_USERNAME, HTTP_PASSWORD))



@swaig.endpoint("Create a new Zendesk ticket",
    subject=SWAIGArgument("string", "The subject of the ticket."),
    comment_body=SWAIGArgument("string", "The body of the initial comment."),
    requester_name=SWAIGArgument("string", "Name of the requester."),
    requester_email=SWAIGArgument("string", "Email of the requester."),
    priority=SWAIGArgument("string", "Priority of the ticket.", required=False))
def create_ticket(subject, comment_body, requester_name, requester_email, priority=None, meta_data_token=None, meta_data=None):
    url = f'https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/tickets.json'
    ticket_data = {
        "ticket": {
            "subject": subject,
            "comment": {
                "body": comment_body
            },
            "requester": {
                "name": requester_name,
                "email": requester_email
            }
        }
    }
    if priority:
        ticket_data["ticket"]["priority"] = priority

    response = requests.post(url, json=ticket_data, auth=zendesk_auth())
    ticket_info = response.json().get('ticket', {})
    return format_ticket_info(ticket_info)

@swaig.endpoint("Update an existing Zendesk ticket",
    ticket_id=SWAIGArgument("integer", "The ID of the ticket to update."),
    status=SWAIGArgument("string", "New status of the ticket.", required=False),
    priority=SWAIGArgument("string", "New priority of the ticket.", required=False),
    comment_body=SWAIGArgument("string", "Additional comment to add.", required=False),
    public=SWAIGArgument("boolean", "Whether the comment is public.", required=False, default=True))
def update_ticket(ticket_id, status=None, priority=None, comment_body=None, public=True, meta_data_token=None, meta_data=None):
    url = f'https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/tickets/{ticket_id}.json'
    ticket_data = {"ticket": {}}
    if status:
        ticket_data["ticket"]["status"] = status
    if priority:
        ticket_data["ticket"]["priority"] = priority
    if comment_body:
        ticket_data["ticket"]["comment"] = {
            "body": comment_body,
            "public": public
        }

    response = requests.put(url, json=ticket_data, auth=zendesk_auth())
    return response

@swaig.endpoint("Close a Zendesk ticket",
    ticket_id=SWAIGArgument("integer", "The ID of the ticket to close."))
def close_ticket(ticket_id, meta_data_token=None, meta_data=None):
    response = update_ticket(ticket_id, status='closed', meta_data_token=meta_data_token, meta_data=meta_data)
    if response.status_code == 200:
        return "Ticket closed successfully"
    else:
        return "Error: Unable to close the ticket. Please try again later."

@swaig.endpoint("Add a comment to a Zendesk ticket",
    ticket_id=SWAIGArgument("integer", "The ID of the ticket to comment on."),
    public=SWAIGArgument("boolean", "Whether the comment is public.", required=False, default=True))
def add_comment(ticket_id, public=True, meta_data_token=None, meta_data=None):
    response = update_ticket(ticket_id, public=public, meta_data_token=meta_data_token, meta_data=meta_data)
    if response.status_code == 200:
        return "The case has been updated with the new information."
    return "Error: Unable to add comment to the ticket. Please try again later."

@swaig.endpoint("Retrieve details of a Zendesk ticket",
    ticket_id=SWAIGArgument("integer", "The ID of the ticket to retrieve."))
def get_ticket(ticket_id, meta_data_token=None, meta_data=None):
    url = f'https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/tickets/{ticket_id}.json'
    response = requests.get(url, auth=zendesk_auth())
    ticket_info = response.json().get('ticket', {})
    return format_ticket_info(ticket_info)

@swaig.endpoint("Verify a support PIN for a user",
    caller_phone_number=SWAIGArgument("string", "The phone number of the caller."),
    entered_pin=SWAIGArgument("integer", "The PIN entered by the caller."))
def verify_support_pin(caller_phone_number, entered_pin, meta_data_token=None, meta_data=None):
    user = find_user_by_phone(caller_phone_number)
    support_pin = user.get('user_fields', {}).get('support_pin')
    
    try:
        entered_pin = int(entered_pin)
        support_pin = int(support_pin)
    except (ValueError, TypeError):
        return "User not verified"

    if support_pin == entered_pin:
        return f"User verified no need to ask for their support PIN any more, user_id: {user.get('id')} requester_email: {user.get('email')} requester_name: {user.get('name')}"
    return "User not verified"

def find_user_by_phone(caller_phone_number):
    url = f'https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/search.json'
    params = {'query': f'type:user phone:"{caller_phone_number}"'}
    response = requests.get(url, params=params, auth=zendesk_auth())
    results = response.json().get('results', [])

    if results:
        user_id = results[0].get('id')
        user_url = f'https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/users/{user_id}.json'
        user_response = requests.get(user_url, auth=zendesk_auth())
        user = user_response.json().get('user', {})
        return user

    return None

@swaig.endpoint("Retrieve ticket numbers for the authenticated user",
    caller_phone_number=SWAIGArgument("string", "The caller's phone number."),
    status=SWAIGArgument("string", "Filter tickets by status.", required=False),
    priority=SWAIGArgument("string", "Filter tickets by priority.", required=False))
def get_current_user_tickets(caller_phone_number, status=None, priority=None, meta_data_token=None, meta_data=None):
    user = find_user_by_phone(caller_phone_number)
    if user:
        user_id = user['id']
        tickets = list_user_tickets(user_id, status=status, priority=priority)
        if tickets:
            formatted_tickets = format_ticket_list(tickets)
            return formatted_tickets

        else:
            return f"No tickets currently open"
    else:
        return f"User not found."

def list_user_tickets(user_id, status=None, priority=None, page=1, per_page=25):
    url = f'https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/users/{user_id}/tickets/requested.json'
    params = {
        'page': page,
        'per_page': per_page
    }
    response = requests.get(url, params=params, auth=zendesk_auth())
    if response.status_code != 200:
        print(f"Failed to retrieve tickets. Status code: {response.status_code}")
        return None

    tickets = response.json().get('tickets', [])
    if status or priority:
        tickets = [
            ticket for ticket in tickets
            if (not status or ticket.get('status') == status) and
               (not priority or ticket.get('priority') == priority)
        ]

    return tickets

def format_ticket_list(tickets):
    return "\n".join(
        f"TicketId: {ticket.get('id')}, Subject: {ticket.get('subject')}, Status: {ticket.get('status')}"
        for ticket in tickets
    )

@app.route('/', methods=['GET'])
@app.route('/swaig', methods=['GET'])
def serve_zendesk_html():
    try:
        return send_file('zendesk.html')
    except Exception as e:
        return jsonify({"error": "Failed to serve zendesk.html"}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)
