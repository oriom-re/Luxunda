from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any
from app.beings.base import Being

@dataclass
class ComponentBeing(Being):
    """Byt komponentu D3.js"""
    
    def __post_init__(self):
        if self.genesis.get('type') != 'component':
            self.genesis['type'] = 'component'
        if 'd3_config' not in self.attributes:
            self.attributes['d3_config'] = {}
        if 'render_data' not in self.attributes:
            self.attributes['render_data'] = {}
    
    def set_d3_config(self, config: Dict[str, Any]):
        """Ustawia konfigurację komponentu D3"""
        self.attributes['d3_config'] = config
    
    def set_render_data(self, data: Dict[str, Any]):
        """Ustawia dane do renderowania"""
        self.attributes['render_data'] = data
        
        # Zapisz w pamięci
        self.memories.append({
            'type': 'data_update',
            'data_size': len(str(data)),
            'timestamp': datetime.now().isoformat()
        })
    
    def generate_d3_code(self) -> str:
        """Generuje kod D3.js dla komponentu"""
        config = self.attributes.get('d3_config', {})
        component_type = config.get('type', 'basic')
        
        if component_type == 'chart':
            return f"""
// D3.js Chart Component for {self.genesis.get('name', 'Unknown')}
const chart = d3.select("#{config.get('container', 'chart')}")
    .append("svg")
    .attr("width", {config.get('width', 400)})
    .attr("height", {config.get('height', 300)});
"""
        elif component_type == 'graph':
            return f"""
// D3.js Graph Component for {self.genesis.get('name', 'Unknown')}
const simulation = d3.forceSimulation()
    .force("link", d3.forceLink().id(d => d.id))
    .force("charge", d3.forceManyBody())
    .force("center", d3.forceCenter({config.get('width', 400)}/2, {config.get('height', 300)}/2));
"""
        else:
            return f"// Basic D3.js component for {self.genesis.get('name', 'Unknown')}"