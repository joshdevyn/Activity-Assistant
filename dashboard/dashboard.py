from flask import Flask, render_template_string
from threading import Thread
import sys
from io import StringIO
import logging

app = Flask('')

console_buffer = []

class DualStream:
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout

    def write(self, data):
        self.original_stdout.write(data)
        console_buffer.append(data)

    def flush(self):
        self.original_stdout.flush()

# Redirect sys.stdout to the custom stream
sys.stdout = DualStream(sys.stdout)

# Suppress Flask logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# HTML template for the dashboard
grouped_dashboard_template = """
<html>
<head>
    <link rel="icon" href="<your-icon-path-here>" type="image/x-icon">
    <title>Console Dashboard</title>
    <script type="text/javascript">
        var autoScroll = true;  // Default is enabled

        function showCommands(file) {
            var tables = document.getElementsByClassName('commands-table');
            for (var i = 0; i < tables.length; i++) {
                tables[i].style.display = 'none';
            }
            document.getElementById(file).style.display = 'block';
        }

        function updateConsoleContent() {
            var xhr = new XMLHttpRequest();
            xhr.open('GET', '/console_content', true);
            xhr.onreadystatechange = function() {
                if (xhr.readyState == 4 && xhr.status == 200) {
                    var iframe = document.getElementById('consoleIframe');
                    var iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                    iframeDoc.body.innerHTML = xhr.responseText;
                    if (autoScroll) {
                        scrollToBottom();
                    }
                }
            }
            xhr.send();
        }

        setInterval(updateConsoleContent, 2000);

        function scrollToBottom() {
            var iframe = document.getElementById('consoleIframe');
            iframe.contentWindow.scrollTo(0, iframe.contentDocument.body.scrollHeight);
        }

        function toggleAutoScroll() {
            autoScroll = !autoScroll;
            var button = document.getElementById('toggleButton');
            button.innerText = autoScroll ? "Disable Autoscroll" : "Enable Autoscroll";
        }
    </script>
    <style>
    .tabs {
        display: flex;
        flex-direction: row;
    }

    .tab {
        padding: 10px;
        border: 1px solid #ddd;
        cursor: pointer;
        margin: 2px;
    }

    .tab:hover {
        background-color: #f9f9f9;
    }

    .commands-table {
        display: none;
        border: 1px solid #eee;
        width: auto;
        margin-left: 20px;
    }

    table {
        width: 100%;
        border-collapse: collapse;
    }

    table, th, td {
        border: 1px solid #ddd;
    }

    th, td {
        padding: 8px;
    }

    th {
        background-color: #f5f5f5;
    }
    </style>
</head>
<body>
    <h1><alt="Bot Icon" style="vertical-align: middle; width: 50px; height: 50px;"> @Activity Assistant Bot Commands</h1>
    <div class="tabs">
        <div class="tab-list">
            {% for file, file_commands in commands_by_file.items() %}
            <div class="tab" onclick="showCommands('{{ file }}')">{{ file }}</div>
            {% endfor %}
        </div>
        <div class="tab-content">
            {% for file, file_commands in commands_by_file.items() %}
            <table class="commands-table" id="{{ file }}">
                <thead>
                    <tr>
                        <th>Command</th>
                        <th>Description</th>
                        <th>Example</th>
                        <th>Arguments</th>
                    </tr>
                </thead>
                <tbody>
                    {% for command, details in file_commands.items() %}
                    <tr>
                        <td>{{ command }}</td>
                        <td>{{ details["description"] or "No description provided" }}</td>
                        <td>{{ details["example"] }}</td>
                        <td>{{ details["arguments_display"] }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endfor %}
        </div>
    </div>
    <h1>Console Output</h1>
    <button id="toggleButton" onclick="toggleAutoScroll()">Disable Autoscroll</button>
    <iframe id="consoleIframe" src="/console_content" width="100%" height="400px"></iframe>
</body>
</html>
"""

@app.route('/console_content')
def console_content():
    # Convert the raw console data to HTML format
    html_console_data = "".join(console_buffer).replace(' ', '&nbsp;').replace('\n', '<br>')
    return html_console_data

@app.route('/')
def main_dashboard():

    commands_by_file = {
        'activityAssistantCogs/active_channels.py': {
            'active_channels': {
                'description': 'Lists the active channels.',
                'example': '!aa active_channels',
                'arguments': []
            }
        },
        'activityAssistantCogs/active_management.py': {
            'active': {
                'description': 'Manages the active channels.',
                'example': '!aa active',
                'arguments': []
            }
        },
        'activityAssistantCogs/blacklists.py': {
            'blacklist': {
                'description': 'Blacklists a channel or member.',
                'example': '!aa blacklist',
                'arguments': [('channel', True), ('member', True)]
            },
            'remove_blacklist': {
                'description': 'Removes a blacklist entry.',
                'example': '!aa remove_blacklist',
                'arguments': [('channel', True), ('member', True)]
            }
        },
        'activityAssistantCogs/pings.py': {
            'pingme': {
                'description': 'Allows the user to receive pings.',
                'example': '!aa pingme',
                'arguments': [('channel', False)]
            },
            'unpingme': {
                'description': 'Stops the user from receiving pings.',
                'example': '!aa unpingme',
                'arguments': [('channel', False)]
            }
        },
        'activityAssistantCogs/reset_positions.py': {
            'reset_positions': {
                'description': 'Resets the position of channels.',
                'example': '!aa reset_positions',
                'arguments': []
            }
        },
        'activityAssistantCogs/return_positions.py': {
            'return_positions': {
                'description': 'Returns the position of channels.',
                'example': '!aa return_positions',
                'arguments': [('channel_id', True), ('category_id', True)]
            }
        },
        'activityAssistantCogs/subscriptions.py': {
            'subscribed_channels': {
                'description': 'Lists the channels a user is subscribed to.',
                'example': '!aa subscribed_channels',
                'arguments': []
            },
            'subscribed_members': {
                'description': 'Lists members subscribed to a channel.',
                'example': '!aa subscribed_members',
                'arguments': [('channel_id', True)]
            }
        },
        'activityAssistantCogs/utility.py': {
            'define': {
                'description': 'Defines a word.',
                'example': '!aa define <word>',
                'arguments': [('word', False)]
            },
            'topic': {
                'description': 'Fetches a random topic.',
                'example': '!aa topic',
                'arguments': []
            }
        },
        'commands/active.py': {
            'pingme': {
                'description': 'Allows the user to receive pings.',
                'example': '!aa pingme',
                'arguments': [('channel', True)]
            },
            'unpingme': {
                'description': 'Stops the user from receiving pings.',
                'example': '!aa unpingme',
                'arguments': [('channel', True)]
            },
            'subscribed_channels': {
                'description': 'Lists the channels a user is subscribed to.',
                'example': '!aa subscribed_channels',
                'arguments': []
            }
        },
        'commands_handler.py': {
            'approve': {
                'description': 'Approves a guild.',
                'example': '!aa approve',
                'arguments': [('guild_id', False)]
            },
            'deny': {
                'description': 'Denies a guild.',
                'example': '!aa deny',
                'arguments': [('guild_id', False)]
            }
        }
    }

    # Process each command to convert arguments into a displayable string
    for file, commands in commands_by_file.items():
        for command, details in commands.items():
            if details["arguments"]:
                example_arg = next((arg[0] for arg in details["arguments"] if not arg[1]), None)
                details["arguments_display"] = ", ".join([arg[0] + (" (Optional)" if arg[1] else " (Required)") for arg in details["arguments"]])
                details["example_with_arg"] = details["example"] + (" " + example_arg if example_arg else "")
            else:
                details["example_with_arg"] = details["example"]
                details["arguments_display"] = "None"
  
    return render_template_string(grouped_dashboard_template, commands_by_file=commands_by_file)


@app.route('/home')
def home():
    return '<p>Now Running...'

def run_app():
    app.run(host='0.0.0.0',port=8106)

def run_dashboard():
    t = Thread(target=run_app)
    t.start()
