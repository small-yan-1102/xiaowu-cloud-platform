"""Debug MySQL connection via SSH - test different auth methods"""
import paramiko
import sys

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('172.16.24.200', 22, username='test', password='wgu4&Q_2', timeout=10)
    print('SSH OK')

    # Test 1: Use MYSQL_PWD environment variable
    pw = '}C7n%7Wklq6P'
    cmd1 = f'MYSQL_PWD="{pw}" mysql -h 172.16.24.61 -u xiaowu_db silverdawn_ams -N -e "SELECT 1 as test;" 2>&1'
    stdin, stdout, stderr = ssh.exec_command(cmd1, timeout=10)
    out1 = stdout.read().decode('utf-8', errors='replace').strip()
    print(f'Test1 (MYSQL_PWD env): [{out1}]')

    # Test 2: Write password to temp cnf file
    write_cnf = "echo -e '[client]\\npassword=}C7n%7Wklq6P' > /tmp/.mytest.cnf && chmod 600 /tmp/.mytest.cnf"
    stdin, stdout, stderr = ssh.exec_command(write_cnf, timeout=5)
    stdout.read()  # wait for completion
    
    cmd2 = 'mysql --defaults-extra-file=/tmp/.mytest.cnf -h 172.16.24.61 -u xiaowu_db silverdawn_ams -N -e "SELECT 1 as test;" 2>&1'
    stdin, stdout, stderr = ssh.exec_command(cmd2, timeout=10)
    out2 = stdout.read().decode('utf-8', errors='replace').strip()
    print(f'Test2 (cnf file): [{out2}]')

    # Test 3: Check if mysql is available
    stdin, stdout, stderr = ssh.exec_command('which mysql 2>&1', timeout=5)
    out3 = stdout.read().decode('utf-8', errors='replace').strip()
    print(f'MySQL path: [{out3}]')

    # Test 4: mysql version
    stdin, stdout, stderr = ssh.exec_command('mysql --version 2>&1', timeout=5)
    out4 = stdout.read().decode('utf-8', errors='replace').strip()
    print(f'MySQL version: [{out4}]')

    # Cleanup
    ssh.exec_command('rm -f /tmp/.mytest.cnf', timeout=5)

    ssh.close()
    print('Done')

if __name__ == '__main__':
    main()
