            }
            
            # Initialize Nornir with the config
            try:
                self.nr = InitNornir(
                    inventory={
                        "plugin": "SimpleInventory",
                        "options": {
                            "host_file": str(config_dir / "inventory" / "hosts.yaml"),
                            "group_file": str(config_dir / "inventory" / "groups.yaml"),
                            "defaults_file": str(config_dir / "inventory" / "defaults.yaml")
                        }
                    },
                    runner={
                        "plugin": "threaded",
                        "options": {
                            "num_workers": self.max_workers
                        }
                    },
                    logging={
                        "enabled": True,
                        "level": "INFO",
                        "loggers": ["nornir"]
                    }
                )
                
                self.logger.debug(f"Nornir initialized with {len(self.nr.inventory.hosts)} hosts")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize Nornir: {e}")
                # Fall back to None - some methods don't require Nornir
                self.nr = None

    def execute_task(self, device, task_function, layer):
        result = {}
        try:
            # Create connection manager
            connection = ConnectionManager(device)
            
            # Connect to device
            if not connection.connect():
                result['error'] = f"Failed to connect to {device['hostname']}"
                return result
            
            try:
                # Execute task
                task_result = task_function(
                    connection=connection,
                    hostname=device['hostname'],
                    layer=layer,
                    output_handler=self.output_handler
                )
                
                # Process result
                result['success'] = task_result.get('success', False)
                result['commands'] = task_result.get('total_commands', 0)
                if not result['success']:
                    result['error'] = task_result.get('error', 'Unknown error')
                    
            finally:
                # Always disconnect
                connection.disconnect()
                
            return result
            
        except Exception as e:
            self.logger.error(f"Task execution failed for {device['hostname']}: {e}")
            result['error'] = str(e)
            return result 