/**
 * LTL SPOT Trace Renderer with Mermaid Diagrams
 * 
 * This module provides functionality to parse SPOT traces and render them
 * as Mermaid flowcharts (linked list style) with cycle back-arrows.
 * 
 * SPOT trace format: prefix;cycle{...}
 * Example: "a;!b;cycle{a&b;!a}" 
 * Renders as: a → ¬b → a∧b → ¬a → (back to a∧b)
 */

class TraceRenderer {
    constructor() {
        this.stateIdCounter = 0;
    }

    /**
     * Check if trace string is an AccountingRequest or HospitalRequest
     * @param {string} traceStr - The trace string
     * @returns {boolean} True if it's an AccountingRequest or HospitalRequest
     */
    isRequest(traceStr) {
        const trimmed = traceStr.trim();
        return trimmed.startsWith('Subject');
    }

    /**
     * Parse and style AccountingRequest or HospitalRequest string with HTML spans
     * @param {string} requestStr - The AccountingRequest or HospitalRequest string
     * @returns {string} HTML-styled request string
     */
    parseRequest(requestStr) {
        let result = requestStr;
        // Style Subject label (the word "Subject" itself)
        result = result.replace(/(\s*)(Subject)(: )(\w+)/g, '$1<span class="request-subject">$2</span>$3$4');
        
        // Style Action label (the word "Action" itself)
        result = result.replace(/(\n\s*)(Action)(: )(\w+)/g, '$1<span class="request-action">$2</span>$3$4');
        
        // Style Resource label (the word "Resource" itself)
        result = result.replace(/(\n\s*)(Resource)(: )(\w+)/g, '$1<span class="request-resource">$2</span>$3$4');
        
        return result;
    }

    /**
     * Parse a SPOT trace string into structured data
     * @param {string} traceStr - The SPOT trace string
     * @returns {Object} Parsed trace with prefix and cycle states
     */
    parseTrace(traceStr) {
        const trimmed = traceStr.trim();
        if (!trimmed) {
            return { prefix: [], cycle: [], hasCycle: false };
        }

        // Split on 'cycle' to separate prefix and cycle parts
        const parts = trimmed.split('cycle');
        const prefixPart = parts[0];
        const cyclePart = parts.length > 1 ? parts[1] : '';

        // Parse prefix states (semicolon-separated)
        const prefixStates = prefixPart
            .split(';')
            .map(s => s.trim())
            .filter(s => s.length > 0)
            .map(state => this.parseState(state));

        // Parse cycle states if present
        let cycleStates = [];
        let hasCycle = false;
        
        if (cyclePart) {
            hasCycle = true;
            // Extract content between { and }
            const cycleMatch = cyclePart.match(/\{([^}]*)\}/);
            if (cycleMatch) {
                const cycleContent = cycleMatch[1];
                cycleStates = cycleContent
                    .split(';')
                    .map(s => s.trim())
                    .filter(s => s.length > 0)
                    .map(state => this.parseState(state));
            }
        }

        return {
            prefix: prefixStates,
            cycle: cycleStates,
            hasCycle: hasCycle
        };
    }

    /**
     * Parse a single state string into a NodeRepr-like object
     * @param {string} stateStr - State string like "a&!b" or "1" or "0"
     * @returns {Object} Parsed state object with ID and display
     */
    parseState(stateStr) {
        const id = `state_${++this.stateIdCounter}`;
        
        // Handle special cases
        if (stateStr === '1') {
            return { id, display: '⊤', raw: stateStr };
        }
        if (stateStr === '0') {
            return { id, display: '⊥', raw: stateStr };
        }
        if (stateStr === '') {
            return { id, display: '∅', raw: stateStr };
        }

        // Parse conjunctions and negations (similar to Python NodeRepr)
        const literals = stateStr.split('&').map(lit => lit.trim());
        const processedLiterals = literals.map(lit => {
            if (lit.startsWith('!')) {
                let litc = lit.slice(1).trim();
                return `**${litc}**.OFF`;
            } 
            return `**${lit}**.ON`;
        });

        const display = processedLiterals
                        .sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()))
                        .join(' \n ');
        
        return {
            id,
            display,
            raw: stateStr
        };
    }

    /**
     * Generate Mermaid code for a parsed trace (flowchart style)
     * @param {Object} trace - Parsed trace object
     * @param {Object} options - Options for code generation
     * @returns {string} Mermaid diagram code
     */
    /**
     * Generate raw trace text from parsed trace object
     * @param {Object} trace - Parsed trace object with prefix and cycle
     * @returns {string} Original raw trace text
     */
    generateRawTraceText(trace) {
        if (trace.prefix.length === 0 && trace.cycle.length === 0) {
            return "Empty trace";
        }
        
        let rawText = "";
        
        // Add prefix states
        if (trace.prefix.length > 0) {
            rawText += trace.prefix.map(state => state.raw).join("; ");
        }
        
        // Add cycle states if present
        if (trace.hasCycle && trace.cycle.length > 0) {
            if (rawText) rawText += "; ";
            rawText += "cycle{" + trace.cycle.map(state => state.raw).join("; ") + "}";
        }
        
        return rawText;
    }

    /**
     * Render a parsed trace as raw text (no Mermaid diagram)
     * @param {Object} trace - Parsed trace object
     * @param {Object} options - Rendering options
     * @param {string} originalTrace - Original trace string (for AccountingRequest)
     * @returns {string} HTML string with raw text and magnification
     */
    renderTrace(trace, options = {}, originalTrace = '') {
        // Check if this is an AccountingRequest
        if (originalTrace && this.isRequest(originalTrace)) {
            const styledRequest = this.parseRequest(originalTrace);
            const traceId = `trace_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            
            return `<div class="raw-trace accounting-request-trace" data-trace-id="${traceId}" title="Click to enlarge"><div class="raw-trace-magnify-icon">🔍</div><pre class="raw-trace-text">${styledRequest}</pre></div>`;
        }
        
        // Generate the original raw trace text for LTL traces
        const rawTrace = this.generateRawTraceText(trace);
        const traceId = `trace_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        
        return `<div class="raw-trace" data-trace-id="${traceId}" title="Click to enlarge"><div class="raw-trace-magnify-icon">🔍</div><pre class="raw-trace-text">${rawTrace}</pre></div>`;
    }

    /**
     * Create and show magnification modal with raw text
     * @param {string} rawTrace - The raw trace text (unused parameter for compatibility)
     * @param {string} originalTrace - The original trace string
     */
    showMagnifiedTrace(rawTrace, originalTrace) {
        // Remove existing modal if present
        const existingModal = document.getElementById('trace-modal');
        if (existingModal) {
            existingModal.remove();
        }

        // Check if this is an AccountingRequest and style it
        let displayContent = originalTrace;
        if (this.isRequest(originalTrace)) {
            displayContent = this.parseRequest(originalTrace);
        }

        // Create modal HTML for raw text display
        const modalHtml = `
            <div id="trace-modal" class="trace-modal-overlay">
                <div class="trace-modal-content">
                    <div class="trace-modal-header">
                        <h5 class="trace-modal-title">Instance Details</h5>
                        <button class="trace-modal-close" aria-label="Close">&times;</button>
                    </div>
                    <div class="trace-modal-body">
                        <div class="trace-modal-text">
                            <pre class="raw-trace-enlarged">${displayContent}</pre>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Inject modal into DOM
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        const modal = document.getElementById('trace-modal');
        const closeBtn = modal.querySelector('.trace-modal-close');

        // Close modal handlers
        const closeModal = () => {
            // Restore body scroll before removing modal
            document.body.style.overflow = '';
            modal.remove();
        };

        closeBtn.addEventListener('click', closeModal);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });

        // Close on Escape key
        document.addEventListener('keydown', function escHandler(e) {
            if (e.key === 'Escape') {
                closeModal();
                document.removeEventListener('keydown', escHandler);
            }
        });

        // Prevent body scroll when modal is open
        document.body.style.overflow = 'hidden';
    }

    /**
     * Apply trace rendering to all elements with ltl-spot-trace class
     * @param {Object} options - Rendering options
     */
    renderAllTraces(options = {}) {
        const traceElements = document.querySelectorAll('.ltl-spot-trace');
        
        traceElements.forEach(element => {
            // Get the original trace from data-word
            let traceText = element.getAttribute('data-word');
            
            // If data-word is missing or empty, try to extract from textContent (but only if not already rendered)
            if (!traceText || traceText.trim() === '') {
                if (!element.classList.contains('ltl-trace-rendered')) {
                    // Fallback: Decode HTML entities from textContent (e.g., &amp; -> &)
                    const tempDiv = document.createElement('div');
                    tempDiv.innerHTML = element.textContent;
                    traceText = tempDiv.textContent || tempDiv.innerText;
                    console.warn('Using fallback trace from textContent for element:', element, 'Trace:', traceText);
                } else {
                    console.warn('Skipping already-rendered element with no data-word:', element);
                    return;
                }
            }
            
            // If still no trace, skip
            if (!traceText || traceText.trim() === '') {
                console.warn('No trace found for element:', element);
                return;
            }
            
            // If already rendered, skip to prevent overwriting
            if (element.classList.contains('ltl-trace-rendered')) {
                return;
            }
            
            const parsed = this.parseTrace(traceText);
            const rendered = this.renderTrace(parsed, options, traceText);
            
            // Set attributes correctly (only once)
            element.setAttribute('data-original', traceText);  // Original SPOT trace
            
            // Log for debugging
            console.log('Original Trace (data-original):', traceText);
            
            element.innerHTML = rendered;
            element.classList.add('ltl-trace-rendered');
            
            // Add click handler for magnification
            element.addEventListener('click', () => {
                this.showMagnifiedTrace(traceText, traceText);
            });
        });
    }

    /**
     * Initialize the trace renderer on page load
     * @param {Object} options - Default rendering options
     */
    static init(options = {}) {
        const renderer = new TraceRenderer();
        
        // Auto-render on DOM ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                renderer.renderAllTraces(options);
            });
        } else {
            renderer.renderAllTraces(options);
        }

        return renderer;
    }
}

// CSS styles for raw text traces and magnification
const TRACE_STYLES = `
<style>
.raw-trace {
    margin: 0.5rem;
    padding: 0.5rem;
    border: 1px solid #dee2e6;
    border-radius: 0.375rem;
    background-color: #ffffff;
    transition: all 0.2s ease;
    cursor: pointer;
    position: relative;
    font-family: "Monaco", "Consolas", "Courier New", monospace;
}

.raw-trace:hover {
    border-color: #0d6efd;
    box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.25);
    background-color: #f8f9fa;
}

.raw-trace-magnify-icon {
    position: absolute;
    top: 0.25rem;
    right: 0.25rem;
    opacity: 0;
    transition: opacity 0.2s ease;
    font-size: 0.75rem;
    color: #6c757d;
    pointer-events: none;
}

.raw-trace:hover .raw-trace-magnify-icon {
    opacity: 0.6;
}

.raw-trace-text {
    margin: 0.5rem;
    padding: 0.5rem;
    white-space: pre-wrap;
    font-family: inherit;
    font-size: 1.1rem;
    color: #333;
}

/* Magnification Modal Styles */
.trace-modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.7);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 9999;
    animation: fadeIn 0.3s ease;
}

.trace-modal-content {
    background-color: white;
    border-radius: 0.5rem;
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
    max-width: 95vw;
    max-height: 95vh;
    width: 800px;
    display: flex;
    flex-direction: column;
    animation: slideIn 0.3s ease;
}

.trace-modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.5rem;
    border-bottom: 1px solid #dee2e6;
}

.trace-modal-title {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 500;
    color: #212529;
}

.trace-modal-close {
    background: none;
    border: none;
    font-size: 1.5rem;
    color: #6c757d;
    cursor: pointer;
    padding: 0;
    width: 2rem;
    height: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 0.25rem;
    transition: all 0.2s ease;
}

.trace-modal-close:hover {
    background-color: #f8f9fa;
    color: #212529;
}

.trace-modal-body {
    padding: 2rem;
    overflow-y: auto;
    flex: 1;
}

.raw-trace-enlarged {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 0.25rem;
    padding: 1.5rem;
    font-size: 1.5rem;
    line-height: 1.5;
    margin: 0;
    font-family: "Monaco", "Consolas", "Courier New", monospace;
    white-space: pre-wrap;
    color: #333;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes slideIn {
    from { 
        opacity: 0;
        transform: scale(0.8) translateY(-2rem);
    }
    to { 
        opacity: 1;
        transform: scale(1) translateY(0);
    }
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .trace-modal-content {
        width: 95vw;
        margin: 1rem;
    }
    
    .trace-modal-body {
        padding: 1rem;
    }
    
    .raw-trace-enlarged {
        font-size: 1rem;
        padding: 1rem;
    }
}
</style>
`;
// Inject styles into document head
if (typeof document !== 'undefined') {
    document.head.insertAdjacentHTML('beforeend', TRACE_STYLES);
}

// Make TraceRenderer available globally
if (typeof window !== 'undefined') {
    window.TraceRenderer = TraceRenderer;
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TraceRenderer;
}