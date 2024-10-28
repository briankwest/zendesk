from flask import Flask, request, jsonify, send_file
from urllib.parse import urlsplit, urlunsplit
import os
import requests
from dotenv import load_dotenv
from flask_httpauth import HTTPBasicAuth

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

# Define the functions for each SWAIG endpoint
def create_ticket(subject, comment_body, requester_name, requester_email, priority=None):
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

def update_ticket(ticket_id, status=None, priority=None, comment_body=None, public=True):
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

def close_ticket(ticket_id):
    response = update_ticket(ticket_id, status='closed')
    if response.status_code == 200:
        return "Ticket closed successfully"
    else:
        return "Error: Unable to close the ticket. Please try again later."

def add_comment(ticket_id, public=True):
    response = update_ticket(ticket_id, public=public)
    if response.status_code == 200:
        return "The case has been updated with the new information."
    return "Error: Unable to add comment to the ticket. Please try again later."

def get_ticket(ticket_id):
    url = f'https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/tickets/{ticket_id}.json'
    response = requests.get(url, auth=zendesk_auth())
    ticket_info = response.json().get('ticket', {})
    return format_ticket_info(ticket_info)

def verify_support_pin(caller_phone_number, entered_pin):
    user = find_user_by_phone(caller_phone_number)
    support_pin = user.get('user_fields', {}).get('support_pin')
    
    # Convert both entered_pin and support_pin to integers for comparison
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

def get_current_user_tickets(caller_phone_number, status=None, priority=None):
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

SWAIG_FUNCTION_SIGNATURES = {
    "create_ticket": {
        "description": "Create a new Zendesk ticket",
        "function": "create_ticket",
        "parameters": {
            "type": "object",
            "properties": {
                "subject": {"type": "string", "description": "The subject of the ticket."},
                "comment_body": {"type": "string", "description": "The body of the initial comment."},
                "requester_name": {"type": "string", "description": "Name of the requester."},
                "requester_email": {"type": "string", "description": "Email of the requester."},
                "priority": {"type": "string", "description": "Priority of the ticket."}
            },
            "required": ["subject", "comment_body", "requester_name", "requester_email"]
        }
    },
    "update_ticket": {
        "description": "Update an existing Zendesk ticket",
        "function": "update_ticket",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "integer", "description": "The ID of the ticket to update."},
                "status": {"type": "string", "description": "New status of the ticket."},
                "priority": {"type": "string", "description": "New priority of the ticket."},
                "comment_body": {"type": "string", "description": "Additional comment to add."}
            },
            "required": ["ticket_id"]
        }
    },
    "close_ticket": {
        "description": "Close a Zendesk ticket",
        "function": "close_ticket",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "integer", "description": "The ID of the ticket to close."}
            },
            "required": ["ticket_id"]
        }
    },
    "add_comment": {
        "description": "Add a comment to a Zendesk ticket",
        "function": "add_comment",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "integer", "description": "The ID of the ticket to comment on."},
                "public": {"type": "boolean", "description": "Whether the comment is public.", "default": True}
            },
            "required": ["ticket_id"]
        }
    },
    "get_ticket": {
        "description": "Retrieve details of a Zendesk ticket",
        "function": "get_ticket",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "integer", "description": "The ID of the ticket to retrieve."}
            },
            "required": ["ticket_id"]
        }
    },
    "verify_support_pin": {
        "description": "Verify a support PIN for a user",
        "function": "verify_support_pin",
        "parameters": {
            "type": "object",
            "properties": {
                "caller_phone_number": {"type": "string", "description": "The phone number of the caller."},
                "entered_pin": {"type": "integer", "description": "The PIN entered by the caller."}
            },
            "required": ["caller_phone_number", "entered_pin"]
        }
    },
    "get_current_user_tickets": {
        "description": "Retrieve ticket numbers for the authenticated user",
        "function": "get_current_user_tickets",
        "parameters": {
            "type": "object",
            "properties": {
                "caller_phone_number": {"type": "string", "description": "The caller's phone number."},
                "status": {"type": "string", "description": "Filter tickets by status.", "enum": ["new", "open", "pending", "hold", "solved", "closed"], "nullable": True},
                "priority": {"type": "string", "description": "Filter tickets by priority.", "enum": ["low", "normal", "high", "urgent"], "nullable": True}
            },
            "required": ["caller_phone_number"]
        }
    }
}

@app.route('/swaig', methods=['POST'])
@auth.verify_password
def swaig_handler():
    data = request.json
    action = data.get('action')
    print(f"Received action: {action}")

    if action == "get_signature":
        requested_functions = data.get("functions")

        if not requested_functions:
            requested_functions = list(SWAIG_FUNCTION_SIGNATURES.keys())
        
        host_url = request.host_url.rstrip('/')  # Get the request host URL

        for func in SWAIG_FUNCTION_SIGNATURES:
            split_url = urlsplit(host_url)

            if HTTP_USERNAME and HTTP_PASSWORD:
                netloc = f"{HTTP_USERNAME}:{HTTP_PASSWORD}@{split_url.netloc}"
            else:
                netloc = split_url.netloc

            new_url = urlunsplit((split_url.scheme, netloc, split_url.path, split_url.query, split_url.fragment))
            SWAIG_FUNCTION_SIGNATURES[func]["web_hook_url"] = f"{new_url}/swaig"
        
        if requested_functions == '':
            requested_functions = avaliable_functions

        response = [
            SWAIG_FUNCTION_SIGNATURES[func] 
            for func in requested_functions 
            if func in SWAIG_FUNCTION_SIGNATURES
        ]

        missing_functions = [
            func for func in requested_functions 
            if func not in SWAIG_FUNCTION_SIGNATURES
        ]

        print(f"missing_functions: {missing_functions}")

        return jsonify(response)

    else:
        function_name = data.get('function')
        print(f"Function name: {function_name}")
        argument = data.get('argument', {})
        params = argument.get('parsed', [{}])[0]
        print(f"Function name: {function_name}, Params: {params}")

        function_map = {
            func_name: globals()[func_name] 
            for func_name in SWAIG_FUNCTION_SIGNATURES.keys() 
            if func_name in globals()
        }
        print(f"Available functions: {list(function_map.keys())}")

        if function_name in function_map:
            try:
                response = function_map[function_name](**params)
                return jsonify({"response": response})
            except TypeError as e:
                print(f"TypeError: {e}")
                return jsonify({"error": f"Invalid parameters for function '{function_name}'"}), 400
            except Exception as e:
                print(f"Exception: {e}")
                return jsonify({"error": "An unexpected error occurred"}), 500
        else:
            return jsonify({"error": "Function not found"}), 404

@app.route('/', methods=['GET'])
@app.route('/swaig', methods=['GET'])
def serve_zendesk_html():
    try:
        return send_file('zendesk.html')
    except Exception as e:
        return jsonify({"error": "Failed to serve zendesk.html"}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)
