# V5evscriptcli

A powerful CLI and web interface for managing EVE-NG network topologies, with a focus on fixing interface mapping issues for Cisco 3725 routers.

## Features

- **Interface Mapping Fix**: Correctly maps Cisco 3725 router interfaces:
  - f0/0 → API index 0
  - f0/1 → API index 1
  - f1/0 → API index 16 (fixed from incorrect index 2)
  - f2/0 → API index 32 (fixed from incorrect index 4)

- **Web Interface**:
  - Visual topology designer with drag-and-drop interface
  - Real-time deployment status updates
  - Interface mapping visualization
  - Multi-user support with authentication
  - Dark mode support

- **CLI Features**:
  - Automated topology deployment
  - Interface mapping correction
  - Configuration management
  - Error handling and logging

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/V5evscriptcli.git
   cd V5evscriptcli
   ```

2. Install dependencies:
   ```bash
   # For CLI only
   pip install -r requirements.txt

   # For web interface
   pip install -r requirements-web.txt
   ```

3. Configure your EVE-NG credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your EVE-NG credentials
   ```

## Usage

### Web Interface

1. Start the web server:
   ```bash
   ./run_web.py
   ```

2. Access the web interface:
   - Open http://localhost:5000 in your browser
   - Default credentials: admin/admin

3. Using the Topology Designer:
   - Drag router icons from the palette to the canvas
   - Click interfaces to create connections
   - Save and load topologies
   - Deploy directly to EVE-NG

### CLI Usage

1. Create a new topology:
   ```bash
   ./v5evscriptcli.py create --name my_topology
   ```

2. Add routers:
   ```bash
   ./v5evscriptcli.py add-router --topology my_topology --type c3725 --name R1
   ```

3. Connect interfaces:
   ```bash
   ./v5evscriptcli.py connect --topology my_topology --router1 R1 --if1 f1/0 --router2 R2 --if2 f0/0
   ```

4. Deploy topology:
   ```bash
   ./v5evscriptcli.py deploy --topology my_topology
   ```

## Development

### Running Tests

```bash
# Run all tests
./run_tests.py

# Run specific test suites
./run_tests.py --web-only
./run_tests.py --unit-only
./run_tests.py --integration-only

# Generate coverage report
./run_tests.py --coverage --html-report
```

### Project Structure

```
V5evscriptcli/
├── docs/                 # Documentation
├── static/              # Web static files
│   ├── css/            # Stylesheets
│   ├── js/             # JavaScript files
│   └── img/            # Images
├── templates/           # Web templates
├── tests/              # Test suite
├── topologies/         # Saved topologies
├── v5evscriptcli.py    # CLI entry point
├── web_app.py          # Web application
├── run_web.py          # Web server runner
└── run_tests.py        # Test runner
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- EVE-NG team for their network emulation platform
- Contributors who helped identify and fix the interface mapping issue 