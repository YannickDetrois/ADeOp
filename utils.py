import paramiko
import wx
import json
import os

def open_dir_dialog():
    app = wx.App(False)
    dialog = wx.DirDialog(None, "Select directory containing run.py", "", style=wx.DD_DEFAULT_STYLE)

    # Check if a directory was selected
    if dialog.ShowModal() == wx.ID_OK:
        directory = dialog.GetPath()  # Get the selected directory
        dialog.Destroy()

        return directory
    else:
        dialog.Destroy()

        return None
    
def save_run_params(directory, run_params):
    with open(os.path.join(directory, 'params.json'), 'w') as json_file:
        json.dump(run_params, json_file, indent=4)

def get_string_run_params(run_params):
    params_json = json.dumps(run_params, indent=4)

    return params_json

def send_command(shell, command):
    """
    Send a command to the interactive shell and wait for its output.
    :param shell: The Paramiko shell object.
    :param command: The command to send.
    :return: The output of the command.
    """
    shell.send(command + "\n")
    output = ""
    while True:
        if shell.recv_ready():
            output += shell.recv(1024).decode()
            # Check for the shell prompt (adjust based on your server's shell, e.g., "$ ", "> ")
            if output.strip().endswith("$"):  # Replace "$" with your prompt
                break
    return output

def connect_remote(password):
    hostname = "haas009.rcp.epfl.ch"
    #username = "adeop"
    username = "yannick"
    port = 22

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port=port, username=username, password=password)
        return ssh  # Return the ssh instance if connection is successful
    except (paramiko.AuthenticationException, paramiko.SSHException, paramiko.socket.error) as e:
        print(f"Connection failed: {e}")
        return None  # Return None if connection fails


def run_remote_commands(sshclient, pop_size, n_gen, run_params):
    """
    Run a series of commands on a remote server via SSH and yield feedback after each command.

    :param pop_size: Population size for the remote script.
    :param n_gen: Number of generations for the remote script.
    :return: Yields status messages for each command executed.
    """

    commands_nohup = [
        "conda activate carbon",
        "cd Documents/AdsorptionModel_TCSA/src/optimisation/",
        f'echo """{get_string_run_params(run_params)}"""" > test.json', # write the new run params to the params file
        f"nohup python run.py --pop_size {pop_size} --n_gen {n_gen} > output.log 2>&1 &"
    ]

    commands = [
        "conda activate carbon", # activate the environment with modeified pymoo, ...
        "cd Documents/AdsorptionModel_TCSA/src/optimisation/", # change to the run.py directory
        f'echo """{get_string_run_params(run_params)}""" > params.json', # write the new run params to the params file
        f"python run.py --pop_size {pop_size} --n_gen {n_gen}" # run optimisation with the new params
    ]

    try:
        shell = sshclient.invoke_shell()

        # Initial server connection output
        initial_output = send_command(shell, "")  # Just to get the initial prompt
        yield f"{initial_output}"

        for cmd in commands:
            output = send_command(shell, cmd)
            if 'python run.py' in cmd:
                yield f"Output for '{cmd}': {output}"

        # Close connection
        shell.close()
        sshclient.close()
        yield "All commands executed and connection closed."

    except paramiko.SSHException as e:
        yield f"SSH error: {e}"
    except Exception as e:
        yield f"General error: {e}"
