// V5evscriptcli Topology Designer

class TopologyConnection {
    constructor(sourceNode, sourceInterface, targetNode, targetInterface) {
        this.id = `conn-${Date.now()}`;
        this.source = sourceNode;
        this.sourceInterface = sourceInterface;
        this.target = targetNode;
        this.targetInterface = targetInterface;
        this.element = null;
    }
    
    createSVGPath() {
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('id', this.id);
        path.setAttribute('class', 'connection-path');
        path.setAttribute('stroke', '#0066cc');
        path.setAttribute('stroke-width', '2');
        path.setAttribute('fill', 'none');
        return path;
    }
    
    updatePath(sourcePos, targetPos) {
        if (!this.element) return;
        
        // Calculate control points for curved path
        const dx = targetPos.x - sourcePos.x;
        const dy = targetPos.y - sourcePos.y;
        const controlPoint1 = {
            x: sourcePos.x + dx * 0.25,
            y: sourcePos.y + dy * 0.1
        };
        const controlPoint2 = {
            x: sourcePos.x + dx * 0.75,
            y: targetPos.y - dy * 0.1
        };
        
        // Create SVG path
        const d = `M ${sourcePos.x},${sourcePos.y} ` +
                  `C ${controlPoint1.x},${controlPoint1.y} ` +
                  `${controlPoint2.x},${controlPoint2.y} ` +
                  `${targetPos.x},${targetPos.y}`;
        
        this.element.setAttribute('d', d);
    }
}

// Interface mapping utility for correct EVE-NG API indices
class InterfaceMapper {
    constructor() {
        this.mappings = {
            'c3725': {
                'f0/0': 0,
                'f0/1': 1,
                'f1/0': 16,  // NM-1FE-TX in slot 1
                'f2/0': 32   // NM-1FE-TX in slot 2
            },
            'c7200': {
                'g0/0': 0, 'g0/1': 1, 'g0/2': 2, 'g0/3': 3,
                'g0/4': 4, 'g0/5': 5
            },
            'c3640': {
                'f0/0': 0, 'f0/1': 1,
                'f1/0': 16, 'f2/0': 32
            },
            'c2691': {
                'f0/0': 0, 'f0/1': 1,
                'f1/0': 16, 'f2/0': 32
            },
            'c1700': {
                'f0/0': 0,
                's1/0': 16, 's1/1': 17
            }
        };
    }
    
    getCorrectIndex(routerType, interfaceName) {
        const routerMappings = this.mappings[routerType];
        if (!routerMappings) {
            console.warn(`Unknown router type: ${routerType}, using default mapping`);
            return this.mappings['c3725'][interfaceName] || 0;
        }
        
        const index = routerMappings[interfaceName];
        if (index === undefined) {
            console.warn(`Unknown interface ${interfaceName} for router ${routerType}`);
            return 0;
        }
        
        return index;
    }
    
    getSupportedInterfaces(routerType) {
        return Object.keys(this.mappings[routerType] || this.mappings['c3725']);
    }
}

class EnhancedTopologyDesigner extends TopologyDesigner {
    constructor(canvasId) {
        super(canvasId);
        
        // Initialize interface mapper for correct EVE-NG API indices
        this.interfaceMapper = new InterfaceMapper();
        
        // Initialize SVG layer for connections
        this.initializeSVGLayer();
        
        // Additional state
        this.connectionMode = false;
        this.connectionStart = null;
        this.connectionStartInterface = null;
        
        // Bind additional event handlers
        this.canvas.addEventListener('mousemove', this.handleMouseMove.bind(this));
        this.canvas.addEventListener('contextmenu', this.handleContextMenu.bind(this));
    }
    
    initializeSVGLayer() {
        this.svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        this.svg.style.position = 'absolute';
        this.svg.style.top = '0';
        this.svg.style.left = '0';
        this.svg.style.width = '100%';
        this.svg.style.height = '100%';
        this.svg.style.pointerEvents = 'none';
        this.canvas.appendChild(this.svg);
        
        // Temporary path for drawing new connections
        this.tempPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        this.tempPath.setAttribute('class', 'temp-connection');
        this.tempPath.setAttribute('stroke', '#0066cc');
        this.tempPath.setAttribute('stroke-width', '2');
        this.tempPath.setAttribute('stroke-dasharray', '5,5');
        this.tempPath.setAttribute('fill', 'none');
        this.svg.appendChild(this.tempPath);
    }
    
    addNode(nodeData) {
        const node = super.addNode(nodeData);
        
        // Store router type for interface mapping
        node.dataset.routerType = nodeData.type;
        
        // Get correct interfaces for this router type
        const supportedInterfaces = this.interfaceMapper.getSupportedInterfaces(nodeData.type);
        
        // Update node interfaces with correct mappings
        const interfacesContainer = node.querySelector('.router-node-interfaces');
        if (interfacesContainer) {
            interfacesContainer.innerHTML = '';
            supportedInterfaces.forEach(iface => {
                const interfaceElement = document.createElement('div');
                interfaceElement.className = 'interface';
                interfaceElement.dataset.interface = iface;
                interfaceElement.dataset.apiIndex = this.interfaceMapper.getCorrectIndex(nodeData.type, iface);
                interfaceElement.innerHTML = `
                    <i class="fas fa-ethernet"></i> ${iface}
                    <small class="text-muted">(${interfaceElement.dataset.apiIndex})</small>
                `;
                interfacesContainer.appendChild(interfaceElement);
            });
        }
        
        // Add interface click handlers
        const interfaces = node.querySelectorAll('.interface');
        interfaces.forEach(iface => {
            iface.addEventListener('click', (e) => {
                e.stopPropagation();
                this.handleInterfaceClick(node, iface);
            });
        });
        
        return node;
    }
    
    handleInterfaceClick(node, interfaceElement) {
        if (!this.connectionMode) {
            // Start new connection
            this.connectionMode = true;
            this.connectionStart = node;
            this.connectionStartInterface = interfaceElement;
            interfaceElement.classList.add('selected');
        } else {
            // Complete connection
            if (node !== this.connectionStart) {
                this.createConnection(
                    this.connectionStart,
                    this.connectionStartInterface.dataset.interface,
                    node,
                    interfaceElement.dataset.interface
                );
            }
            
            // Reset connection mode
            this.connectionMode = false;
            this.connectionStart = null;
            this.connectionStartInterface.classList.remove('selected');
            this.connectionStartInterface = null;
            this.tempPath.setAttribute('d', '');
        }
    }
    
    createConnection(sourceNode, sourceInterface, targetNode, targetInterface) {
        const connection = new TopologyConnection(
            sourceNode.id,
            sourceInterface,
            targetNode.id,
            targetInterface
        );
        
        // Store the correct API indices for this connection
        const sourceApiIndex = this.interfaceMapper.getCorrectIndex(
            sourceNode.dataset.routerType, 
            sourceInterface
        );
        const targetApiIndex = this.interfaceMapper.getCorrectIndex(
            targetNode.dataset.routerType, 
            targetInterface
        );
        
        connection.sourceApiIndex = sourceApiIndex;
        connection.targetApiIndex = targetApiIndex;
        
        connection.element = connection.createSVGPath();
        this.svg.appendChild(connection.element);
        
        this.connections.set(connection.id, connection);
        this.updateConnections(sourceNode.id);
        this.updateConnections(targetNode.id);
        
        // Notify about new connection with correct indices
        this.onConnectionCreated(connection);
        
        // Update connection list in UI
        this.updateConnectionsList();
    }
    
    handleMouseMove(event) {
        if (this.connectionMode) {
            const rect = this.canvas.getBoundingClientRect();
            const mouseX = event.clientX - rect.left;
            const mouseY = event.clientY - rect.top;
            
            const startRect = this.connectionStartInterface.getBoundingClientRect();
            const startX = startRect.left + startRect.width / 2 - rect.left;
            const startY = startRect.top + startRect.height / 2 - rect.top;
            
            // Update temporary connection path
            const d = `M ${startX},${startY} L ${mouseX},${mouseY}`;
            this.tempPath.setAttribute('d', d);
        }
    }
    
    handleContextMenu(event) {
        event.preventDefault();
        
        if (this.connectionMode) {
            // Cancel connection
            this.connectionMode = false;
            this.connectionStart = null;
            this.connectionStartInterface.classList.remove('selected');
            this.connectionStartInterface = null;
            this.tempPath.setAttribute('d', '');
        }
    }
    
    updateConnections(nodeId) {
        super.updateConnections(nodeId);
        
        const node = this.nodes.get(nodeId);
        if (!node) return;
        
        this.connections.forEach(connection => {
            if (connection.source === nodeId || connection.target === nodeId) {
                const sourceNode = this.nodes.get(connection.source);
                const targetNode = this.nodes.get(connection.target);
                
                if (sourceNode && targetNode) {
                    const sourceInterface = sourceNode.querySelector(`[data-interface="${connection.sourceInterface}"]`);
                    const targetInterface = targetNode.querySelector(`[data-interface="${connection.targetInterface}"]`);
                    
                    if (sourceInterface && targetInterface) {
                        const sourceRect = sourceInterface.getBoundingClientRect();
                        const targetRect = targetInterface.getBoundingClientRect();
                        const canvasRect = this.canvas.getBoundingClientRect();
                        
                        const sourcePos = {
                            x: sourceRect.left + sourceRect.width / 2 - canvasRect.left,
                            y: sourceRect.top + sourceRect.height / 2 - canvasRect.top
                        };
                        
                        const targetPos = {
                            x: targetRect.left + targetRect.width / 2 - canvasRect.left,
                            y: targetRect.top + targetRect.height / 2 - canvasRect.top
                        };
                        
                        connection.updatePath(sourcePos, targetPos);
                    }
                }
            }
        });
    }
    
    onConnectionCreated(connection) {
        // Event handler for new connections with correct API indices
        console.log('Connection created with correct mapping:', {
            source: connection.source,
            sourceInterface: connection.sourceInterface,
            sourceApiIndex: connection.sourceApiIndex,
            target: connection.target,
            targetInterface: connection.targetInterface,
            targetApiIndex: connection.targetApiIndex
        });
    }
    
    updateConnectionsList() {
        const connectionsList = document.getElementById('connectionsList');
        if (!connectionsList) return;
        
        connectionsList.innerHTML = '';
        
        this.connections.forEach(connection => {
            const sourceNode = this.nodes.get(connection.source);
            const targetNode = this.nodes.get(connection.target);
            
            if (sourceNode && targetNode) {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${sourceNode.querySelector('.router-node-name').textContent}</td>
                    <td>${connection.sourceInterface} (${connection.sourceApiIndex})</td>
                    <td>${targetNode.querySelector('.router-node-name').textContent}</td>
                    <td>${connection.targetInterface} (${connection.targetApiIndex})</td>
                    <td>
                        <button class="btn btn-sm btn-danger" onclick="window.topologyDesigner.removeConnection('${connection.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                `;
                connectionsList.appendChild(row);
            }
        });
    }
    
    removeConnection(connectionId) {
        const connection = this.connections.get(connectionId);
        if (connection && connection.element) {
            connection.element.remove();
            this.connections.delete(connectionId);
            this.updateConnectionsList();
        }
    }
    
    getTopologyData() {
        const data = {
            nodes: {},
            connections: [],
            interfaceMappings: {},  // Store interface mappings for persistence
            version: '1.0',         // Version for compatibility
            created: new Date().toISOString()
        };
        
        // Collect node data with router types and interface mappings
        this.nodes.forEach((node, id) => {
            const rect = node.getBoundingClientRect();
            const canvasRect = this.canvas.getBoundingClientRect();
            const routerType = node.dataset.routerType || 'c3725';
            
            data.nodes[id] = {
                id: id,
                type: routerType,
                name: node.querySelector('.router-node-name').textContent,
                position: {
                    x: rect.left - canvasRect.left,
                    y: rect.top - canvasRect.top
                },
                interfaces: this.interfaceMapper.getSupportedInterfaces(routerType)
            };
            
            // Store interface mappings for this router
            data.interfaceMappings[id] = {};
            const interfaces = node.querySelectorAll('.interface');
            interfaces.forEach(iface => {
                const interfaceName = iface.dataset.interface;
                const apiIndex = this.interfaceMapper.getCorrectIndex(routerType, interfaceName);
                data.interfaceMappings[id][interfaceName] = apiIndex;
            });
        });
        
        // Collect connection data with API indices
        this.connections.forEach(connection => {
            data.connections.push({
                id: connection.id,
                source: connection.source,
                sourceInterface: connection.sourceInterface,
                sourceApiIndex: connection.sourceApiIndex,
                target: connection.target,
                targetInterface: connection.targetInterface,
                targetApiIndex: connection.targetApiIndex
            });
        });
        
        return data;
    }
    
    loadTopologyData(data) {
        // Clear existing topology
        this.nodes.forEach(node => node.remove());
        this.connections.forEach(connection => connection.element.remove());
        this.nodes.clear();
        this.connections.clear();
        
        // Validate data format
        if (!data.nodes || !data.connections) {
            console.error('Invalid topology data format');
            return;
        }
        
        // Load nodes with correct interface mappings
        Object.entries(data.nodes).forEach(([id, nodeData]) => {
            const node = this.addNode(nodeData);
            
            // Position the node correctly relative to canvas
            node.style.position = 'absolute';
            node.style.left = `${nodeData.position.x}px`;
            node.style.top = `${nodeData.position.y}px`;
            
            // Restore interface mappings if available
            if (data.interfaceMappings && data.interfaceMappings[id]) {
                const interfaces = node.querySelectorAll('.interface');
                interfaces.forEach(iface => {
                    const interfaceName = iface.dataset.interface;
                    const savedIndex = data.interfaceMappings[id][interfaceName];
                    if (savedIndex !== undefined) {
                        iface.dataset.apiIndex = savedIndex;
                        // Update display to show correct index
                        const indexDisplay = iface.querySelector('small');
                        if (indexDisplay) {
                            indexDisplay.textContent = `(${savedIndex})`;
                        }
                    }
                });
            }
        });
        
        // Load connections with correct API indices
        data.connections.forEach(connData => {
            const sourceNode = this.nodes.get(connData.source);
            const targetNode = this.nodes.get(connData.target);
            
            if (sourceNode && targetNode) {
                const connection = new TopologyConnection(
                    connData.source,
                    connData.sourceInterface,
                    connData.target,
                    connData.targetInterface
                );
                
                // Restore API indices
                connection.sourceApiIndex = connData.sourceApiIndex || 
                    this.interfaceMapper.getCorrectIndex(sourceNode.dataset.routerType, connData.sourceInterface);
                connection.targetApiIndex = connData.targetApiIndex || 
                    this.interfaceMapper.getCorrectIndex(targetNode.dataset.routerType, connData.targetInterface);
                
                connection.element = connection.createSVGPath();
                this.svg.appendChild(connection.element);
                
                this.connections.set(connection.id, connection);
            }
        });
        
        // Update all connections and UI
        this.nodes.forEach((node, id) => {
            this.updateConnections(id);
        });
        this.updateConnectionsList();
        
        console.log('Topology loaded with preserved interface mappings');
    }
}

// Initialize topology designer when the page loads
document.addEventListener('DOMContentLoaded', function() {
    const topologyCanvas = document.getElementById('topologyCanvas');
    if (topologyCanvas) {
        window.topologyDesigner = new EnhancedTopologyDesigner('topologyCanvas');
        
        // Add router palette with correct interface mappings
        const palette = document.getElementById('routerPalette');
        if (palette) {
            const routerTypes = ['c3725', 'c7200', 'c3640', 'c2691', 'c1700'];
            routerTypes.forEach(type => {
                const button = document.createElement('button');
                button.className = 'btn btn-outline-primary mb-2 w-100';
                button.innerHTML = `
                    <span class="badge badge-router-${type} me-2">${type}</span>
                    Add Router
                `;
                button.onclick = () => {
                    const id = `router-${Date.now()}`;
                    const supportedInterfaces = window.topologyDesigner.interfaceMapper.getSupportedInterfaces(type);
                    
                    window.topologyDesigner.addNode({
                        id: id,
                        type: type,
                        name: `R${window.topologyDesigner.nodes.size + 1}`,
                        interfaces: supportedInterfaces
                    });
                };
                palette.appendChild(button);
            });
        }
        
        // Enhanced save topology functionality
        const saveButton = document.getElementById('saveTopology');
        if (saveButton) {
            saveButton.onclick = () => {
                const data = window.topologyDesigner.getTopologyData();
                
                // Send to server via WebSocket or HTTP
                if (window.socket && window.socket.connected) {
                    window.socket.emit('save_topology', data);
                } else {
                    // Fallback to HTTP API
                    fetch('/api/topology/save', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(data)
                    })
                    .then(response => response.json())
                    .then(result => {
                        if (result.success) {
                            showAlert(`Topology saved as ${result.filename}`, 'success');
                        } else {
                            showAlert(`Failed to save topology: ${result.error}`, 'danger');
                        }
                    })
                    .catch(error => {
                        console.error('Save error:', error);
                        showAlert('Failed to save topology', 'danger');
                    });
                }
            };
        }
    }
}); 