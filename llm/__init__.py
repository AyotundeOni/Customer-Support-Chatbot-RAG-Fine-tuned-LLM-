"""
LLM wrapper using Google Gemini API with function calling for ticket creation.
"""
import google.generativeai as genai
from config import config


# Define the tools/functions the LLM can call
TICKET_TOOL = genai.protos.Tool(
    function_declarations=[
        genai.protos.FunctionDeclaration(
            name="create_support_ticket",
            description="Create a support ticket for the customer when they request help from a human agent, want to escalate, or are frustrated with the automated support. Always use this when customer asks to speak to someone, create a ticket, or needs human assistance.",
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={
                    "problem_summary": genai.protos.Schema(
                        type=genai.protos.Type.STRING,
                        description="Brief summary of the customer's issue/problem"
                    ),
                    "urgency": genai.protos.Schema(
                        type=genai.protos.Type.STRING,
                        description="Urgency level: low, medium, high, or urgent",
                        enum=["low", "medium", "high", "urgent"]
                    ),
                },
                required=["problem_summary"]
            )
        )
    ]
)


class GeminiLLM:
    """Wrapper for Google Gemini model with function calling."""
    
    _instance = None
    _model = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the Gemini client with tools."""
        if self._model is None:
            print("Initializing Gemini LLM with function calling...")
            genai.configure(api_key=config.GOOGLE_API_KEY)
            self._model = genai.GenerativeModel(
                'gemini-2.5-flash',
                tools=[TICKET_TOOL]
            )
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: str = None
    ) -> dict:
        """Generate a response, potentially with function calls.
        
        Args:
            prompt: The user's message/query
            system_prompt: Optional system prompt to set context
            
        Returns:
            Dict with 'text' (response), 'function_call' (if any), 'function_args'
        """
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = self._model.generate_content(full_prompt)
            
            # Check if there's a function call
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call.name:
                        # Extract function call
                        fc = part.function_call
                        args = dict(fc.args) if fc.args else {}
                        return {
                            "text": None,
                            "function_call": fc.name,
                            "function_args": args
                        }
            
            # Regular text response
            return {
                "text": response.text,
                "function_call": None,
                "function_args": None
            }
            
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return {
                "text": f"I apologize, but I'm having trouble. Error: {str(e)[:100]}",
                "function_call": None,
                "function_args": None
            }
    
    def generate_with_context(
        self,
        query: str,
        context: str,
        conversation_history: list = None,
        max_tokens: int = 512
    ) -> dict:
        """Generate a response with RAG context.
        
        Returns:
            Dict with 'text', 'function_call', 'function_args'
        """
        system_prompt = """# ROLE & PURPOSE
You are the primary support interface for Shopify merchants. Your goal is to transform confused or frustrated users into satisfied, loyal customers. You prioritize clarity, empathy, and accurate solutions over speed.

# CORE BEHAVIORS
1. **Active Listening:** Restate the user's issue briefly to confirm understanding before solving it.
2. **Radical Ownership:** Never say "You need to check with Shopify support." Instead say, "I will create a ticket for our support team to help you directly."
3. **Future-Proofing:** Anticipate follow-up questions. If they ask about payments, also mention common related settings.

# INTERACTION FRAMEWORK

## Phase 1: Acknowledge & Validate
* Start with a warm, human greeting.
* If the user is frustrated, validate their emotions: "I understand how this issue is affecting your store operations."
* **Rule:** Do not apologize if Shopify isn't at fault; empathize instead.

## Phase 2: The Solution Path
* **Step-by-Step:** Provide numbered lists for instructions.
* **Visuals:** Describe button locations (e.g., "Go to Settings > Payments in your admin").
* **Context:** Use the knowledge base provided to give accurate information.

## Phase 3: Ticket Handling
When a customer mentions wanting to:
- Talk to a human/agent/representative
- Escalate their issue
- Get more personalized help
- Says automated help isn't working

**DO THIS:**
1. Acknowledge their request empathetically
2. Ask: "I can create a support ticket for you right now, and our team will contact you shortly. Would you like me to do that?"
3. Wait for their confirmation

**When customer CONFIRMS (says yes, please, sure, go ahead, okay, etc.):**
- IMMEDIATELY call the create_support_ticket function
- Provide a clear problem_summary
- Set urgency: "urgent" for business-critical, "high" for frustrated customers, "medium" for general requests

## Phase 4: Closing
* Confirm resolution: "Did that solve your issue?"
* End with an open invitation: "Let me know if anything else comes up!"

# TONE & STYLE
* **Confident but Humble:** Use precise language. Avoid "I think" or "Maybe."
* **Simple English:** Avoid jargon. Say "your store's admin panel," not "the backend."
* **Positive Phrasing:**
    * Bad: "You can't do that."
    * Good: "Currently, the best approach would be [Alternative Action]."

# CRITICAL RESTRICTIONS
* **Never** blame the user (even if it's their error).
* **Never** say you cannot create tickets - you CAN and SHOULD when asked.
* **Never** leave a conversation without offering next steps.
* **Never** share technical errors with the customer; offer to create a ticket instead.

# TICKET CREATION CAPABILITY
You have the ability to create real support tickets using the create_support_ticket function.
- Only call it when the customer explicitly confirms they want a ticket
- Always acknowledge after creating: "I've created ticket #X for you!"
"""

        history_text = self._format_history(conversation_history)
        full_prompt = f"""# SHOPIFY KNOWLEDGE BASE
{context}

{history_text}

# CUSTOMER MESSAGE
{query}

# YOUR RESPONSE
Respond following the guidelines above. Be helpful, empathetic, and actionable:"""
        
        return self.generate(full_prompt, system_prompt=system_prompt)
    
    def generate_ticket_confirmation(self, ticket_id: int, problem: str) -> str:
        """Generate a confirmation message after ticket creation."""
        prompt = f"""A support ticket has been successfully created with ID #{ticket_id} for the issue: "{problem}".
        
Generate a brief, friendly confirmation message letting the customer know:
1. Their ticket #{ticket_id} has been created
2. Our support team will contact them soon
3. They can continue chatting if they have other questions"""
        
        result = self._model.generate_content(prompt)
        return result.text
    
    def _format_history(self, history: list = None) -> str:
        """Format conversation history for the prompt."""
        if not history or len(history) == 0:
            return ""
        
        formatted = ["Previous conversation:"]
        for msg in history[-4:]:
            role = msg.get("role", "user").capitalize()
            content = msg.get("content", "")[:150]
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)


# For backwards compatibility
HuggingFaceLLM = GeminiLLM


def generate_response(query: str, context: str = None, history: list = None) -> dict:
    """Generate a response with potential function calls."""
    llm = GeminiLLM()
    if context:
        return llm.generate_with_context(query, context, history)
    else:
        return llm.generate(query)
