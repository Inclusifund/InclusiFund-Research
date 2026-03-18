#!/bin/bash
# ============================================================================
# QUANTUM GRANT MATCHING SETUP - CLAUDE CODE + CURSOR
# ============================================================================
# 
# This script sets up your local environment for quantum-powered grant
# matching integrated with your existing Convex backend and Obsidian vault.
#
# Location: ~/Inclusi-funding Vault/InclusiFund-Vault/
# ============================================================================

echo "🚀 Setting up Quantum Grant Matching in Claude Code..."
echo ""

# ============================================================================
# STEP 1: Create Obsidian-Centric Project Structure
# ============================================================================

echo "📁 Creating Obsidian-centric project structure..."

# Navigate to your vault
cd "$HOME/Inclusi-funding Vault/InclusiFund-Vault" || exit

# Create Obsidian folders (markdown-first)
mkdir -p "Research/Quantum Research"
mkdir -p "Research/Training Logs"
mkdir -p "Projects/Quantum Grant Matching"
mkdir -p "Data/Quantum"
mkdir -p "Skills/Quantum"
mkdir -p "Agents"

# Create code directories
mkdir -p quantum_grants/{models,data,circuits,training,utils}
mkdir -p quantum_grants/convex_integration

echo "✅ Obsidian-centric structure created:"
echo ""
echo "📓 OBSIDIAN (Markdown):"
echo "   Research/"
echo "   ├── Quantum Research/         # Experiment notes"
echo "   └── Training Logs/            # Daily progress"
echo "   Projects/"
echo "   └── Quantum Grant Matching/   # Master project doc"
echo "   Data/"
echo "   └── Quantum/                  # Data catalog (markdown)"
echo "   Skills/"
echo "   └── Quantum/                  # Quantum skills"
echo "   Agents/"
echo "   └── Agent_9_Quantum_Matcher.md"
echo ""
echo "💻 CODE (Python):"
echo "   quantum_grants/"
echo "   ├── models/                   # Python models"
echo "   ├── circuits/                 # Quantum circuits"
echo "   ├── training/                 # Training scripts"
echo "   └── convex_integration/       # Convex sync"
echo ""

# ============================================================================
# STEP 2: Install Origin Quantum Python SDK (Local)
# ============================================================================

echo "📦 Installing Origin Quantum Python SDK locally..."
echo ""

# Create virtual environment
python3 -m venv quantum_grants/venv
source quantum_grants/venv/bin/activate

# Install Origin Quantum libraries
echo "Installing QPanda (quantum programming framework)..."
pip install pyqpanda --break-system-packages

echo "Installing VQNet (quantum machine learning)..."
pip install pyvqnet --break-system-packages

# Install supporting libraries
echo "Installing supporting libraries..."
pip install pandas numpy matplotlib scikit-learn --break-system-packages

# Install Convex Python client (if not already installed)
pip install convex --break-system-packages

echo ""
echo "✅ Origin Quantum SDK installed locally!"
echo "   - QPanda: Quantum circuits and simulation"
echo "   - VQNet: Quantum-classical hybrid ML"
echo "   - You can now run quantum code WITHOUT cloud upload"
echo ""

# ============================================================================
# STEP 3: Create Convex Integration Script
# ============================================================================

echo "🔗 Creating Convex integration..."

cat > quantum_grants/convex_integration/fetch_grants.py << 'EOF'
"""
Convex Grant Data Fetcher
==========================

Fetches grant data from your Convex backend for quantum training.
"""

import os
from convex import ConvexClient
import pandas as pd

# Convex configuration
CONVEX_URL = os.getenv('CONVEX_URL', 'https://your-convex-url.convex.cloud')

def get_convex_client():
    """Initialize Convex client."""
    return ConvexClient(CONVEX_URL)

def fetch_all_grants():
    """
    Fetch all grants from Convex.
    
    Returns:
        pandas.DataFrame: Grant data
    """
    client = get_convex_client()
    
    # Query your grants table (adjust query name to match your Convex schema)
    grants = client.query("grants:list")
    
    # Convert to DataFrame
    df = pd.DataFrame(grants)
    
    print(f"✅ Fetched {len(df)} grants from Convex")
    
    return df

def fetch_cic_profiles():
    """
    Fetch CIC profiles from Convex.
    
    Returns:
        pandas.DataFrame: CIC profile data
    """
    client = get_convex_client()
    
    # Query your CICs table
    cics = client.query("cics:list")
    
    df = pd.DataFrame(cics)
    
    print(f"✅ Fetched {len(df)} CIC profiles from Convex")
    
    return df

def save_local_cache(df, filename):
    """Save data locally for offline training."""
    cache_dir = "../data"
    os.makedirs(cache_dir, exist_ok=True)
    
    filepath = os.path.join(cache_dir, filename)
    df.to_csv(filepath, index=False)
    
    print(f"💾 Cached to: {filepath}")

if __name__ == "__main__":
    # Fetch data
    grants_df = fetch_all_grants()
    cics_df = fetch_cic_profiles()
    
    # Cache locally
    save_local_cache(grants_df, 'grants_convex.csv')
    save_local_cache(cics_df, 'cics_convex.csv')
    
    print("\n✅ Data ready for quantum training!")
EOF

chmod +x quantum_grants/convex_integration/fetch_grants.py

echo "✅ Convex integration script created!"
echo ""

# ============================================================================
# STEP 4: Create Quantum Circuit Template
# ============================================================================

echo "🔬 Creating quantum circuit template..."

cat > quantum_grants/circuits/grant_matcher_circuit.py << 'EOF'
"""
Quantum Grant Matching Circuit
================================

Variational Quantum Circuit (VQC) for matching CIC profiles to grants.
"""

from pyqpanda import *
import numpy as np

class QuantumGrantMatcherCircuit:
    """
    Quantum circuit for grant-CIC matching using VQC.
    
    This uses parameterized quantum gates that learn to recognize
    patterns in grant-CIC compatibility.
    """
    
    def __init__(self, num_qubits=4):
        """
        Initialize quantum circuit.
        
        Args:
            num_qubits (int): Number of qubits (more = more features)
        """
        self.num_qubits = num_qubits
        
        # Initialize quantum machine (CPU simulator)
        self.qm = CPUQVM()
        self.qm.init_qvm()
        
        # Allocate qubits
        self.qubits = self.qm.qAlloc_many(num_qubits)
        
        # Build circuit
        self.circuit = self._build_circuit()
        
        print(f"✅ Quantum circuit initialized: {num_qubits} qubits")
    
    def _build_circuit(self):
        """Build the variational quantum circuit."""
        
        cir = QCircuit()
        
        # Layer 1: Feature encoding (Hadamard superposition)
        for i in range(self.num_qubits):
            cir << H(self.qubits[i])
        
        # Layer 2: Entanglement
        for i in range(self.num_qubits - 1):
            cir << CNOT(self.qubits[i], self.qubits[i+1])
        
        # Layer 3: Parameterized rotations (trainable)
        # These parameters will be optimized during training
        for i in range(self.num_qubits):
            cir << RY(self.qubits[i], 0.0)  # Will be parameterized
            cir << RZ(self.qubits[i], 0.0)
        
        # Layer 4: More entanglement
        for i in range(self.num_qubits - 1):
            cir << CNOT(self.qubits[i], self.qubits[i+1])
        
        return cir
    
    def run(self, input_features, parameters):
        """
        Run quantum circuit with given parameters.
        
        Args:
            input_features (array): Input feature vector
            parameters (array): Trainable circuit parameters
            
        Returns:
            float: Quantum circuit output (match score)
        """
        # Encode input features into quantum state
        # (Implementation details here)
        
        # Apply parameterized gates
        # (Training will optimize these parameters)
        
        # Measure output
        # (Returns match probability)
        
        pass  # Full implementation in training script

if __name__ == "__main__":
    # Test circuit creation
    circuit = QuantumGrantMatcherCircuit(num_qubits=4)
    print(circuit.circuit)
EOF

echo "✅ Quantum circuit template created!"
echo ""

# ============================================================================
# STEP 5: Create Claude Code Prompt
# ============================================================================

echo "📝 Creating Claude Code prompt..."

cat > quantum_grants/CLAUDE_CODE_PROMPT.md << 'EOF'
# Claude Code Prompt: Quantum Grant Matching

Hey Claude, I need help building a quantum-powered grant matching system.

## Context

I have:
- **Convex backend** with grants and CIC profiles
- **Obsidian vault** at `~/Inclusi-funding Vault/InclusiFund-Vault/`
- **Origin Quantum Python SDK** installed locally (QPanda + VQNet)
- **8-agent swarm** for grant automation
- **800+ Antigravity skills** in the vault

## Goal

Build a quantum-classical hybrid model that:
1. Fetches grant data from Convex
2. Trains quantum circuit to match CICs to grants
3. Achieves better accuracy than classical matching
4. Integrates as Agent 9 in my swarm

## Project Structure

```
quantum_grants/
├── convex_integration/
│   └── fetch_grants.py          # ✅ Created
├── circuits/
│   └── grant_matcher_circuit.py # ✅ Created
├── models/
│   └── hybrid_model.py          # ⏳ Need to create
├── training/
│   └── train_quantum.py         # ⏳ Need to create
└── utils/
    └── feature_engineering.py   # ⏳ Need to create
```

## Tasks

### Task 1: Feature Engineering
Create `utils/feature_engineering.py`:
- Extract features from grant data (amount, deadline, sectors, etc.)
- Extract features from CIC profiles (beneficiaries, activities, etc.)
- Normalize features for quantum circuit input (0-1 range)

### Task 2: Hybrid Model
Create `models/hybrid_model.py`:
- Use VQNet to build quantum-classical hybrid network
- Classical layer → Quantum circuit → Classical output
- Training loop with Adam optimizer

### Task 3: Training Script
Create `training/train_quantum.py`:
- Load data from Convex (via fetch_grants.py)
- Split train/test sets
- Train quantum model
- Compare vs. classical baseline
- Save trained model

### Task 4: Integration
Create new agent: `agents/quantum_grant_matcher_agent.py`
- Loads trained quantum model
- Receives CIC profile
- Returns top 20 grant matches
- Integrates with existing 8-agent swarm

## Constraints

- Keep all data local (don't upload to Origin Quantum cloud)
- Use Convex as source of truth
- Integrate with existing vault structure
- Make it work with Claude Code workflow

## Success Criteria

- [ ] Quantum model trains successfully
- [ ] Accuracy > classical baseline by 5%+
- [ ] Integrates with Convex backend
- [ ] Works as Agent 9 in swarm
- [ ] Can run locally via Claude Code

Let's build this step by step!
EOF

echo "✅ Claude Code prompt created: quantum_grants/CLAUDE_CODE_PROMPT.md"
echo ""

# ============================================================================
# STEP 6: Create Quick Start Guide
# ============================================================================

cat > quantum_grants/README.md << 'EOF'
# Quantum Grant Matching - Quick Start

## Setup (One-Time)

```bash
# 1. Navigate to project
cd ~/Inclusi-funding\ Vault/InclusiFund-Vault/quantum_grants

# 2. Activate virtual environment
source venv/bin/activate

# 3. Set Convex URL
export CONVEX_URL="your-convex-deployment-url"
```

## Workflow

### Step 1: Fetch Data from Convex
```bash
python convex_integration/fetch_grants.py
```

### Step 2: Train Quantum Model
```bash
python training/train_quantum.py
```

### Step 3: Test Model
```bash
python models/test_model.py
```

### Step 4: Integrate with Agent Swarm
```bash
# Model automatically available to Agent 9
```

## Using with Claude Code

Open Cursor and run:
```
claude code start quantum_grants/
```

Then prompt Claude Code with:
```
Build the quantum grant matching system following CLAUDE_CODE_PROMPT.md
```

Claude Code will:
1. Read your existing vault structure
2. Access Convex data
3. Build quantum models
4. Integrate with agent swarm
EOF

echo "✅ README created!"
echo ""

# ============================================================================
# DONE
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 SETUP COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📁 Project location:"
echo "   ~/Inclusi-funding Vault/InclusiFund-Vault/quantum_grants/"
echo ""
echo "✅ Installed:"
echo "   - Origin Quantum Python SDK (local)"
echo "   - QPanda & VQNet"
echo "   - Convex integration"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Open Cursor:"
echo "   cd ~/Inclusi-funding\ Vault/InclusiFund-Vault/"
echo "   cursor ."
echo ""
echo "2. Open Claude Code and load:"
echo "   quantum_grants/CLAUDE_CODE_PROMPT.md"
echo ""
echo "3. Fetch data from Convex:"
echo "   source quantum_grants/venv/bin/activate"
echo "   python quantum_grants/convex_integration/fetch_grants.py"
echo ""
echo "4. Let Claude Code build the rest!"
echo ""
echo "🚀 Ready to build quantum-powered grant matching!"
echo ""
