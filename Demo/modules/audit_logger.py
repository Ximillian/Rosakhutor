import csv
import os
from datetime import datetime

class AuditLogger:
    def __init__(self, config):
        self.log_file = config.get('audit_csv')
        self.fieldnames = ['timestamp', 'operator', 'action', 'ticket_number', 'details']
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writeheader()

    def log(self, operator, action, ticket_number, details=""):
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writerow({
                'timestamp': datetime.now().isoformat(),
                'operator': operator,
                'action': action,
                'ticket_number': ticket_number,
                'details': details
            })