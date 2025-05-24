# NetAuditPro - Network Device Audit Tool

NetAuditPro is a comprehensive network device audit and configuration management tool designed to connect to Cisco IOS devices, collect configurations, and provide reporting on the collected data.

## Features

- Connect to network devices via SSH through a jump host
- Verify device connectivity via ICMP
- Collect and store device configurations
- Filter inventory based on hostname, IP, and device type
- Display audit results with graphical summaries
- Automatically handle unreachable devices
- Generate detailed reports

## Getting Started

### Prerequisites

- Python 3.10+
- Flask
- Paramiko
- Netmiko
- Playwright

### Installation

1. Clone this repository:
```bash
git clone https://github.com/zumanm1/device-audit-win.git
cd device-audit-win
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

### Running the Application

```bash
python rr4-router-enhanced.py
```

The application will be available at http://localhost:5007

## Inventory Configuration

Place your network device inventory in the `inventories` directory in CSV format with the following fields:
- hostname
- ip
- device_type
- username
- password
- port
- enable_secret

## License

This project is proprietary software.

## Acknowledgments

- Built with Flask
- Uses Netmiko for device connections
- Employs Paramiko for SSH operations
