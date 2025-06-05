// V5evscriptcli Web Dashboard JavaScript

// Global variables
let socket = null;
let deploymentUpdateHandlers = new Map();
let topologyDesigner = null;

// ============================================================================
// SOCKET.IO REAL-TIME COMMUNICATION
// ============================================================================

function initializeSocket() {
    if (!socket) {
        socket = io();
        
        socket.on('connect', () => {
            console.log('Connected to V5evscriptcli Dashboard');
            updateConnectionStatus('connected');
        });
        
        socket.on('disconnect', () => {
            console.log('Disconnected from dashboard');
            updateConnectionStatus('disconnected');
        });
        
        socket.on('deployment_update', handleDeploymentUpdate);
        socket.on('deployment_complete', handleDeploymentComplete);
        socket.on('deployment_error', handleDeploymentError);
    }
}

function updateConnectionStatus(status) {
    const statusElement = document.getElementById('connectionStatus');
    if (statusElement) {
        statusElement.className = `badge bg-${status === 'connected' ? 'success' : 'danger'}`;
        statusElement.textContent = status === 'connected' ? 'Connected' : 'Disconnected';
    }
}

// ============================================================================
// DEPLOYMENT MANAGEMENT
// ============================================================================

function handleDeploymentUpdate(data) {
    const handler = deploymentUpdateHandlers.get(data.deployment_id);
    if (handler) {
        handler(data);
    }
    
    // Update progress bars and status indicators
    updateDeploymentProgress(data);
    
    // Add to activity feed
    addActivityFeedItem({
        type: 'info',
        message: data.message || 'Deployment update received',
        timestamp: new Date()
    });
}

function handleDeploymentComplete(data) {
    updateDeploymentProgress({
        deployment_id: data.deployment_id,
        status: 'completed',
        progress: 100
    });
    
    addActivityFeedItem({
        type: 'success',
        message: `Lab "${data.lab_name}" deployed successfully!`,
        timestamp: new Date()
    });
    
    showAlert('Deployment completed successfully!', 'success');
}

function handleDeploymentError(data) {
    updateDeploymentProgress({
        deployment_id: data.deployment_id,
        status: 'failed',
        progress: 0
    });
    
    addActivityFeedItem({
        type: 'error',
        message: `Deployment failed: ${data.error}`,
        timestamp: new Date()
    });
    
    showAlert(`Deployment failed: ${data.error}`, 'danger');
}

function updateDeploymentProgress(data) {
    const progressElement = document.getElementById(`progress-${data.deployment_id}`);
    const statusElement = document.getElementById(`status-${data.deployment_id}`);
    
    if (progressElement) {
        progressElement.style.width = `${data.progress}%`;
        progressElement.setAttribute('aria-valuenow', data.progress);
        progressElement.textContent = `${data.progress}%`;
    }
    
    if (statusElement) {
        statusElement.textContent = data.status;
        statusElement.className = `badge deployment-status-${data.status}`;
    }
}

// ============================================================================
// TOPOLOGY DESIGNER
// ============================================================================

class TopologyDesigner {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.nodes = new Map();
        this.connections = new Map();
        this.selectedNode = null;
        this.dragStartPos = null;
        
        if (!this.canvas) {
            throw new Error(`Canvas element with ID '${canvasId}' not found`);
        }
        
        this.initializeCanvas();
    }
    
    initializeCanvas() {
        this.canvas.addEventListener('dragover', this.handleDragOver.bind(this));
        this.canvas.addEventListener('drop', this.handleDrop.bind(this));
        this.canvas.addEventListener('click', this.handleCanvasClick.bind(this));
        
        // Ensure canvas has relative positioning for absolute positioned nodes
        this.canvas.style.position = 'relative';
    }
    
    addNode(nodeData) {
        const node = document.createElement('div');
        node.className = 'router-node';
        node.draggable = true;
        node.id = `node-${nodeData.id}`;
        node.style.position = 'absolute';
        node.style.left = '100px';
        node.style.top = '100px';
        
        node.innerHTML = `
            <div class="router-node-header">
                <span class="badge badge-router-${nodeData.type}">${nodeData.type}</span>
                <span class="router-node-name">${nodeData.name}</span>
                <button class="btn btn-sm btn-outline-danger float-end" onclick="window.topologyDesigner.removeNode('${nodeData.id}')">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="router-node-interfaces">
                ${this.renderInterfaces(nodeData.interfaces || ['f0/0', 'f0/1'])}
            </div>
        `;
        
        node.addEventListener('dragstart', this.handleDragStart.bind(this));
        node.addEventListener('dragend', this.handleDragEnd.bind(this));
        node.addEventListener('click', this.handleNodeClick.bind(this));
        
        this.canvas.appendChild(node);
        this.nodes.set(nodeData.id, node);
        
        return node;
    }
    
    removeNode(nodeId) {
        const node = this.nodes.get(nodeId);
        if (node) {
            // Remove all connections involving this node
            const connectionsToRemove = [];
            this.connections.forEach((connection, id) => {
                if (connection.source === nodeId || connection.target === nodeId) {
                    connectionsToRemove.push(id);
                }
            });
            
            connectionsToRemove.forEach(connId => {
                this.removeConnection(connId);
            });
            
            // Remove the node
            node.remove();
            this.nodes.delete(nodeId);
            
            // Update connections list if it exists
            if (this.updateConnectionsList) {
                this.updateConnectionsList();
            }
        }
    }
    
    removeConnection(connectionId) {
        const connection = this.connections.get(connectionId);
        if (connection && connection.element) {
            connection.element.remove();
            this.connections.delete(connectionId);
        }
    }
    
    renderInterfaces(interfaces) {
        return interfaces.map(iface => `
            <div class="interface" data-interface="${iface}">
                <i class="fas fa-ethernet"></i> ${iface}
            </div>
        `).join('');
    }
    
    handleDragStart(event) {
        this.selectedNode = event.target.closest('.router-node');
        if (!this.selectedNode) return;
        
        const rect = this.selectedNode.getBoundingClientRect();
        const canvasRect = this.canvas.getBoundingClientRect();
        
        this.dragStartPos = {
            x: event.clientX - (rect.left - canvasRect.left),
            y: event.clientY - (rect.top - canvasRect.top)
        };
        
        event.dataTransfer.setData('text/plain', this.selectedNode.id);
        event.dataTransfer.effectAllowed = 'move';
        
        // Add dragging class for visual feedback
        this.selectedNode.classList.add('dragging');
    }
    
    handleDragOver(event) {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
    }
    
    handleDrop(event) {
        event.preventDefault();
        
        if (this.selectedNode && this.dragStartPos) {
            const canvasRect = this.canvas.getBoundingClientRect();
            const x = Math.max(0, Math.min(
                event.clientX - canvasRect.left - this.dragStartPos.x,
                this.canvas.clientWidth - this.selectedNode.offsetWidth
            ));
            const y = Math.max(0, Math.min(
                event.clientY - canvasRect.top - this.dragStartPos.y,
                this.canvas.clientHeight - this.selectedNode.offsetHeight
            ));
            
            this.selectedNode.style.left = `${x}px`;
            this.selectedNode.style.top = `${y}px`;
            
            this.updateConnections(this.selectedNode.id.replace('node-', ''));
        }
    }
    
    handleDragEnd(event) {
        if (this.selectedNode) {
            this.selectedNode.classList.remove('dragging');
        }
        this.selectedNode = null;
        this.dragStartPos = null;
    }
    
    handleNodeClick(event) {
        // Select/deselect node
        this.deselectAll();
        const node = event.target.closest('.router-node');
        if (node) {
            node.classList.add('selected');
            this.selectedNode = node;
        }
    }
    
    handleCanvasClick(event) {
        if (event.target === this.canvas) {
            this.deselectAll();
        }
    }
    
    deselectAll() {
        this.nodes.forEach(node => {
            node.classList.remove('selected');
        });
        this.selectedNode = null;
    }
    
    updateConnections(nodeId) {
        // Base implementation - can be overridden by subclasses
        // This method should update any visual connections when a node moves
        console.log(`Updating connections for node: ${nodeId}`);
    }
    
    clearTopology() {
        // Remove all nodes and connections
        this.nodes.forEach(node => node.remove());
        this.connections.forEach(connection => {
            if (connection.element) {
                connection.element.remove();
            }
        });
        this.nodes.clear();
        this.connections.clear();
        
        // Update UI
        if (this.updateConnectionsList) {
            this.updateConnectionsList();
        }
    }
    
    getTopologyData() {
        // Base implementation
        const data = {
            nodes: {},
            connections: [],
            version: '1.0',
            created: new Date().toISOString()
        };
        
        this.nodes.forEach((node, id) => {
            const rect = node.getBoundingClientRect();
            const canvasRect = this.canvas.getBoundingClientRect();
            
            data.nodes[id] = {
                id: id,
                type: node.querySelector('.badge').textContent,
                name: node.querySelector('.router-node-name').textContent,
                position: {
                    x: rect.left - canvasRect.left,
                    y: rect.top - canvasRect.top
                }
            };
        });
        
        return data;
    }
    
    loadTopologyData(data) {
        // Base implementation
        this.clearTopology();
        
        if (!data || !data.nodes) {
            console.error('Invalid topology data');
            return;
        }
        
        Object.entries(data.nodes).forEach(([id, nodeData]) => {
            const node = this.addNode(nodeData);
            node.style.left = `${nodeData.position.x}px`;
            node.style.top = `${nodeData.position.y}px`;
        });
    }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function showAlert(message, type = 'info') {
    const alertContainer = document.createElement('div');
    alertContainer.innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    const container = document.querySelector('.container-fluid');
    if (container) {
        container.insertAdjacentElement('afterbegin', alertContainer.firstElementChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = alertContainer.firstElementChild;
            if (alert) {
                alert.remove();
            }
        }, 5000);
    }
}

function addActivityFeedItem(item) {
    const feed = document.getElementById('activityFeed');
    if (!feed) return;
    
    const itemElement = document.createElement('div');
    itemElement.className = 'border-bottom pb-2 mb-2';
    itemElement.innerHTML = `
        <div class="d-flex justify-content-between">
            <div>
                <i class="fas fa-${getActivityIcon(item.type)} text-${item.type} me-2"></i>
                ${item.message}
            </div>
            <small class="text-muted">${formatTimestamp(item.timestamp)}</small>
        </div>
    `;
    
    // Remove "no activity" message if present
    const noActivity = feed.querySelector('.text-center');
    if (noActivity) {
        noActivity.remove();
    }
    
    // Add new item at the top
    feed.insertBefore(itemElement, feed.firstChild);
    
    // Keep only last 10 items
    while (feed.children.length > 10) {
        feed.removeChild(feed.lastChild);
    }
}

function getActivityIcon(type) {
    switch (type) {
        case 'success': return 'check-circle';
        case 'error': return 'exclamation-circle';
        case 'warning': return 'exclamation-triangle';
        default: return 'info-circle';
    }
}

function formatTimestamp(date) {
    return date.toLocaleTimeString();
}

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Socket.IO connection
    initializeSocket();
    
    // Initialize Topology Designer if on topology page
    const topologyCanvas = document.getElementById('topologyCanvas');
    if (topologyCanvas) {
        topologyDesigner = new TopologyDesigner('topologyCanvas');
    }
    
    // Set active navigation link
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}); 