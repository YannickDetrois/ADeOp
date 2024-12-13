import paramiko

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

def run_remote_commands(pop_size, n_gen):
    """
    Run a series of commands on a remote server via SSH and yield feedback after each command.

    :param pop_size: Population size for the remote script.
    :param n_gen: Number of generations for the remote script.
    :return: Yields status messages for each command executed.
    """

    hostname = "haas009.rcp.epfl.ch"
    username = "yannick"
    password = "wFGipyyS4R" 
    port = 22

    commands_nohup = [
        "conda activate carbon",
        "cd Documents/AdsorptionModel_TCSA/src/optimisation/",
        "git pull",
        f"nohup python run.py --pop_size {pop_size} --n_gen {n_gen} > output.log 2>&1 &"
    ]

    commands = [
        "conda activate carbon",
        "cd Documents/AdsorptionModel_TCSA/src/optimisation/",
        "git pull",
        f"python run.py --pop_size {pop_size} --n_gen {n_gen}"
    ]

    try:

        # Connect to the server
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port=port, username=username, password=password)

        shell = ssh.invoke_shell()

        # Initial server connection output
        initial_output = send_command(shell, "")  # Just to get the initial prompt
        yield f"{initial_output}"

        for cmd in commands:
            output = send_command(shell, cmd)
            if 'python run.py' in cmd:
                yield f"Output for '{cmd}': {output}"

        # Close connection
        shell.close()
        ssh.close()
        yield "All commands executed and connection closed."

    except paramiko.SSHException as e:
        yield f"SSH error: {e}"
    except Exception as e:
        yield f"General error: {e}"
