#!/usr/bin/python3
import os
import pwd
import grp


def get_user_and_group_ids(user, group):
    """Retrieves the numerical user and group IDs.

    Args:
      user (str): The username.
      group (str): The group name.

    Returns:
      A tuple of (uid, gid).
    """

    try:
        pw_entry = pwd.getpwnam(user)
        gr_entry = grp.getgrnam(group)
        return pw_entry.pw_uid, gr_entry.gr_gid
    except KeyError:
        print(f"Error: User or group not found: {user}, {group}")
        return None, None


def create_upsd_users_file(username, password):
    """Creates the /etc/nut/upsd.users file with the specified user and password.

    Args:
      username (str): The username for the UPS user.
      password (str): The password for the UPS user.
    """

    file_path = "/etc/nut/upsd.users"

    try:
        with open(file_path, "w") as f:
            f.write(f"[{username}]\n")
            f.write(f"    password = {password}\n")
            f.write("    actions = SET\n")
            f.write("    instcmds = ALL\n")

        # Set permissions and ownership
        os.chmod(file_path, 0o640)  # Set permissions

        uid, gid = get_user_and_group_ids("nut", "nut")
        if uid is not None and gid is not None:
            os.chown(file_path, uid, gid)  # Set ownership to nut:nut

        print(f"UPS user '{username}' created successfully in {file_path}")
    except OSError as e:
        print(f"Error creating UPS user: {e}")


def get_env_var(var_name):
    """Retrieves an environment variable and exits if it's not set.

    Args:
      var_name: The name of the environment variable.

    Returns:
      The value of the environment variable.

    Raises:
      SystemExit: If the environment variable is not set.
    """

    value = os.environ.get(var_name)
    if value is None:
        print(f"Error: Environment variable '{var_name}' is not set.")
        exit(1)
    return value


if __name__ == "__main__":
    UPS_USERNAME = get_env_var("UPS_USERNAME")
    UPS_PASSWORD = get_env_var("UPS_PASSWORD")

    create_upsd_users_file(UPS_USERNAME, UPS_PASSWORD)
