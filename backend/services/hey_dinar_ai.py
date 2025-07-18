import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import uuid

@dataclass
class ChatMessage:
    id: str
    user_id: str
    message: str
    response: str
    timestamp: datetime
    context_data: Dict[str, Any]
    intent: str
    confidence: float

class HeyDinarAI:
    """
    AI Money Concierge service for financial assistance
    Provides natural language processing for financial queries
    """
    
    def __init__(self):
        self.intent_patterns = {
            'balance_inquiry': [
                r'\b(balance|money|funds|how much|total)\b.*\b(have|got|available|left)\b',
                r'\b(what.s|whats|show|tell me).*\b(balance|money|funds)\b',
                r'\b(current|total|available).*\b(balance|funds)\b'
            ],
            'spending_inquiry': [
                r'\b(how much|what.*spend|spent|spending)\b.*\b(today|this week|this month|yesterday)\b',
                r'\b(expenses|spending|spent).*\b(today|week|month|year)\b',
                r'\b(money spent|expenditure|outgoing)\b'
            ],
            'transaction_history': [
                r'\b(show|list|display|view).*\b(transactions|payments|history|activity)\b',
                r'\b(recent|last|latest).*\b(transactions|payments|activity)\b',
                r'\b(transaction|payment).*\b(history|list|record)\b'
            ],
            'category_analysis': [
                r'\b(category|categories|spending on|spent on).*\b(grocery|food|fuel|shopping|restaurant)\b',
                r'\b(how much|what.*spend).*\b(grocery|food|fuel|shopping|restaurant)\b',
                r'\b(breakdown|analysis|summary).*\b(spending|expenses)\b'
            ],
            'affordability_check': [
                r'\b(can I afford|afford|enough money|sufficient funds)\b',
                r'\b(should I buy|can I buy|able to buy)\b',
                r'\b(budget|within budget|over budget)\b'
            ],
            'savings_inquiry': [
                r'\b(savings|saved|saving|save)\b.*\b(rate|amount|how much)\b',
                r'\b(how much.*save|saving|saved)\b',
                r'\b(savings account|savings balance)\b'
            ],
            'exchange_rates': [
                r'\b(exchange rate|currency|convert|USD|EUR|GBP)\b',
                r'\b(rate|conversion|foreign currency)\b',
                r'\b(dollars|euros|pounds|currency)\b'
            ],
            'financial_advice': [
                r'\b(advice|recommend|suggest|should I)\b.*\b(financial|money|investment)\b',
                r'\b(financial planning|budgeting|investment)\b',
                r'\b(help|tips|guidance).*\b(financial|money)\b'
            ],
            'greeting': [
                r'\b(hello|hi|hey|good morning|good afternoon|good evening|greetings)\b',
                r'\b(hey dinar|hello dinar|hi dinar)\b'
            ],
            'goodbye': [
                r'\b(goodbye|bye|see you|thanks|thank you|bye bye)\b',
                r'\b(that.s all|nothing else|end|stop)\b'
            ],
            'help': [
                r'\b(help|what can you do|commands|options)\b',
                r'\b(how to|how do I|assist|support)\b'
            ]
        }
        
        self.response_templates = {
            'greeting': [
                "Hello! I'm Hey Dinar, your AI financial assistant. How can I help you manage your money today?",
                "Hi there! I'm Hey Dinar, here to help you with your finances. What would you like to know?",
                "Greetings! I'm Hey Dinar, your personal financial concierge. How may I assist you today?",
                "Hello! I'm Hey Dinar, ready to help you make smart financial decisions. What can I do for you?"
            ],
            'goodbye': [
                "Goodbye! Feel free to ask me anything about your finances anytime.",
                "See you later! I'm always here to help with your financial questions.",
                "Thank you for using Hey Dinar! Have a great day managing your finances!",
                "Bye! Remember, I'm here 24/7 to help you with your money matters."
            ],
            'help': [
                "I can help you with various financial tasks:\n• Check your balance across all accounts\n• Analyze your spending patterns\n• Review recent transactions\n• Provide budget advice\n• Check exchange rates\n• Assess affordability of purchases\n\nJust ask me in natural language!",
                "Here's what I can do for you:\n• 'What's my balance?' - Check your account balances\n• 'How much did I spend this month?' - Analyze spending\n• 'Show recent transactions' - View transaction history\n• 'Can I afford this?' - Budget assessment\n• 'Exchange rates' - Currency information\n\nFeel free to ask me anything about your finances!"
            ]
        }
    
    def classify_intent(self, message: str) -> tuple[str, float]:
        """Classify user intent based on message content"""
        message_lower = message.lower()
        best_intent = 'unknown'
        best_confidence = 0.0
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    # Simple confidence scoring based on pattern matches
                    confidence = 0.8 if len(re.findall(pattern, message_lower)) > 0 else 0.6
                    if confidence > best_confidence:
                        best_intent = intent
                        best_confidence = confidence
        
        return best_intent, best_confidence
    
    def get_balance_response(self, context_data: Dict[str, Any]) -> str:
        """Generate response for balance inquiries"""
        wallet_balance = context_data.get('wallet_balance', {})
        open_banking_data = context_data.get('open_banking_data', {})
        
        jd_balance = wallet_balance.get('jd_balance', 0)
        dinarx_balance = wallet_balance.get('dinarx_balance', 0)
        
        response = f"Here's your current balance overview:\n\n"
        response += f"💰 **Your DinarX Wallet:**\n"
        response += f"• JD Balance: {jd_balance:.2f} JOD\n"
        response += f"• DinarX Balance: {dinarx_balance:.2f} DINARX\n\n"
        
        if open_banking_data and open_banking_data.get('has_linked_accounts'):
            total_bank_balance = open_banking_data.get('total_balance', 0)
            accounts = open_banking_data.get('accounts', [])
            
            response += f"🏦 **Your Bank Accounts:**\n"
            for account in accounts:
                response += f"• {account['bank_name']}: {account['balance']:.2f} JOD\n"
            
            response += f"\n💎 **Total Across All Accounts:** {total_bank_balance:.2f} JOD"
            
            if jd_balance > 0 or dinarx_balance > 0:
                grand_total = total_bank_balance + jd_balance + dinarx_balance
                response += f"\n🌟 **Grand Total (Including Wallet):** {grand_total:.2f} JOD"
        else:
            response += "💡 Connect your bank accounts for a complete financial overview!"
        
        return response
    
    def get_spending_response(self, context_data: Dict[str, Any], timeframe: str = "month") -> str:
        """Generate response for spending inquiries"""
        open_banking_data = context_data.get('open_banking_data', {})
        
        if not open_banking_data or not open_banking_data.get('has_linked_accounts'):
            return "To analyze your spending patterns, please connect your bank accounts through the Open Banking feature."
        
        transactions = open_banking_data.get('recent_transactions', [])
        
        # Filter transactions by timeframe
        now = datetime.now()
        if timeframe == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif timeframe == "week":
            start_date = now - timedelta(days=7)
        elif timeframe == "month":
            start_date = now - timedelta(days=30)
        else:
            start_date = now - timedelta(days=30)
        
        # Calculate spending
        total_spending = 0
        spending_by_category = {}
        
        for tx in transactions:
            tx_date = datetime.fromisoformat(tx['transaction_date'].replace('Z', '+00:00'))
            if tx_date >= start_date and tx['amount'] < 0:  # Negative amounts are expenses
                amount = abs(tx['amount'])
                total_spending += amount
                
                # Simple category classification based on merchant
                merchant = tx.get('merchant', 'Other').lower()
                category = self.classify_transaction_category(merchant)
                spending_by_category[category] = spending_by_category.get(category, 0) + amount
        
        response = f"💸 **Your Spending Analysis ({timeframe}):**\n\n"
        response += f"**Total Spent:** {total_spending:.2f} JOD\n\n"
        
        if spending_by_category:
            response += "**Spending by Category:**\n"
            sorted_categories = sorted(spending_by_category.items(), key=lambda x: x[1], reverse=True)
            for category, amount in sorted_categories:
                percentage = (amount / total_spending) * 100 if total_spending > 0 else 0
                response += f"• {category}: {amount:.2f} JOD ({percentage:.1f}%)\n"
        
        if total_spending > 0:
            avg_daily = total_spending / 30 if timeframe == "month" else total_spending / 7 if timeframe == "week" else total_spending
            response += f"\n📊 **Average Daily Spending:** {avg_daily:.2f} JOD"
        
        return response
    
    def classify_transaction_category(self, merchant: str) -> str:
        """Classify transaction into categories based on merchant"""
        merchant_lower = merchant.lower()
        
        if any(word in merchant_lower for word in ['carrefour', 'grocery', 'supermarket', 'market']):
            return "🛒 Groceries"
        elif any(word in merchant_lower for word in ['restaurant', 'cafe', 'food', 'fakhr']):
            return "🍽️ Dining"
        elif any(word in merchant_lower for word in ['total', 'fuel', 'gas', 'petrol']):
            return "⛽ Fuel"
        elif any(word in merchant_lower for word in ['atm', 'bank', 'withdrawal']):
            return "🏧 ATM/Banking"
        elif any(word in merchant_lower for word in ['amazon', 'shopping', 'online']):
            return "🛍️ Shopping"
        elif any(word in merchant_lower for word in ['zain', 'mobile', 'phone', 'telecom']):
            return "📱 Telecom"
        elif any(word in merchant_lower for word in ['edco', 'utility', 'electric', 'water']):
            return "🔌 Utilities"
        elif any(word in merchant_lower for word in ['transfer', 'family', 'personal']):
            return "👥 Transfers"
        elif any(word in merchant_lower for word in ['investment', 'return', 'dividend']):
            return "📈 Investment"
        else:
            return "📦 Other"
    
    def get_transaction_history_response(self, context_data: Dict[str, Any]) -> str:
        """Generate response for transaction history requests"""
        open_banking_data = context_data.get('open_banking_data', {})
        
        if not open_banking_data or not open_banking_data.get('has_linked_accounts'):
            return "To view your transaction history, please connect your bank accounts through the Open Banking feature."
        
        transactions = open_banking_data.get('recent_transactions', [])[:10]  # Last 10 transactions
        
        if not transactions:
            return "I don't see any recent transactions in your connected accounts."
        
        response = "📋 **Your Recent Transactions:**\n\n"
        
        for tx in transactions:
            amount = tx['amount']
            date = datetime.fromisoformat(tx['transaction_date'].replace('Z', '+00:00'))
            formatted_date = date.strftime("%b %d, %Y")
            
            emoji = "➕" if amount > 0 else "➖"
            color = "green" if amount > 0 else "red"
            
            response += f"{emoji} **{tx['description']}**\n"
            response += f"   Amount: {amount:.2f} JOD\n"
            response += f"   Date: {formatted_date}\n"
            response += f"   Account: {tx.get('account_name', 'Unknown')}\n"
            response += f"   Merchant: {tx.get('merchant', 'N/A')}\n\n"
        
        return response
    
    def get_affordability_response(self, context_data: Dict[str, Any], amount: float = None) -> str:
        """Generate response for affordability checks"""
        wallet_balance = context_data.get('wallet_balance', {})
        open_banking_data = context_data.get('open_banking_data', {})
        
        total_available = wallet_balance.get('jd_balance', 0)
        
        if open_banking_data and open_banking_data.get('has_linked_accounts'):
            total_available += open_banking_data.get('total_balance', 0)
        
        if amount is None:
            return f"💰 **Available for Spending:**\n\nYou have {total_available:.2f} JOD available across all your accounts.\n\n💡 **Tip:** Tell me a specific amount to check if you can afford it!"
        
        if total_available >= amount:
            remaining = total_available - amount
            return f"✅ **You can afford it!**\n\nPurchase amount: {amount:.2f} JOD\nAvailable balance: {total_available:.2f} JOD\nRemaining after purchase: {remaining:.2f} JOD\n\n💡 This looks affordable based on your current balance!"
        else:
            shortfall = amount - total_available
            return f"❌ **Insufficient funds**\n\nPurchase amount: {amount:.2f} JOD\nAvailable balance: {total_available:.2f} JOD\nShortfall: {shortfall:.2f} JOD\n\n💡 Consider adding funds to your wallet or checking your spending budget."
    
    def get_exchange_rates_response(self, context_data: Dict[str, Any]) -> str:
        """Generate response for exchange rate inquiries"""
        exchange_rates = context_data.get('exchange_rates', {})
        
        if not exchange_rates:
            return "📊 **Current Exchange Rates (JOD):**\n\nI'm unable to fetch current exchange rates. Please try again later."
        
        rates = exchange_rates.get('rates', {})
        last_updated = exchange_rates.get('last_updated', '')
        
        response = "💱 **Current Exchange Rates (JOD):**\n\n"
        
        rate_emojis = {
            'USD': '🇺🇸',
            'EUR': '🇪🇺',
            'GBP': '🇬🇧',
            'SAR': '🇸🇦',
            'AED': '🇦🇪',
            'KWD': '🇰🇼',
            'QAR': '🇶🇦'
        }
        
        for currency, rate in rates.items():
            emoji = rate_emojis.get(currency, '💰')
            response += f"{emoji} **{currency}**: {rate:.4f}\n"
        
        if last_updated:
            update_time = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            response += f"\n🕐 **Last updated:** {update_time.strftime('%b %d, %Y %I:%M %p')}"
        
        response += "\n\n💡 **Tip:** You can exchange currencies directly in your wallet!"
        
        return response
    
    def get_financial_advice_response(self, context_data: Dict[str, Any]) -> str:
        """Generate financial advice based on user's financial situation"""
        wallet_balance = context_data.get('wallet_balance', {})
        open_banking_data = context_data.get('open_banking_data', {})
        
        advice = "💡 **Financial Advice:**\n\n"
        
        # Check if user has linked accounts
        if not open_banking_data or not open_banking_data.get('has_linked_accounts'):
            advice += "🏦 **Connect your bank accounts** through Open Banking to get personalized insights!\n\n"
        
        # Balance analysis
        jd_balance = wallet_balance.get('jd_balance', 0)
        dinarx_balance = wallet_balance.get('dinarx_balance', 0)
        
        if jd_balance > 0 and dinarx_balance == 0:
            advice += "💰 **Consider diversifying:** You have JD in your wallet. Consider converting some to DinarX for international transactions.\n\n"
        
        # Spending pattern advice
        if open_banking_data and open_banking_data.get('recent_transactions'):
            transactions = open_banking_data['recent_transactions']
            total_spending = sum(abs(tx['amount']) for tx in transactions if tx['amount'] < 0)
            
            if total_spending > 0:
                advice += f"📊 **Spending insights:** You've spent {total_spending:.2f} JOD recently. Consider tracking your expenses by category.\n\n"
        
        # General financial tips
        advice += "🎯 **General Tips:**\n"
        advice += "• Use the 50/30/20 rule: 50% needs, 30% wants, 20% savings\n"
        advice += "• Review your transactions regularly\n"
        advice += "• Set up automatic savings transfers\n"
        advice += "• Keep 3-6 months of expenses as emergency fund\n"
        advice += "• Use DinarX for international transfers to save on fees"
        
        return advice
    
    def extract_amount_from_message(self, message: str) -> Optional[float]:
        """Extract monetary amount from user message"""
        # Look for patterns like "100 JOD", "50.5", "$100", etc.
        patterns = [
            r'(\d+\.?\d*)\s*(?:JOD|jod|dinars?|د\.أ)',
            r'(\d+\.?\d*)\s*(?:USD|usd|dollars?|\$)',
            r'(\d+\.?\d*)\s*(?:EUR|eur|euros?|€)',
            r'(\d+\.?\d*)\s*(?:GBP|gbp|pounds?|£)',
            r'(\d+\.?\d*)',  # Plain number
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    def extract_timeframe_from_message(self, message: str) -> str:
        """Extract timeframe from user message"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['today', 'this day']):
            return 'today'
        elif any(word in message_lower for word in ['this week', 'week', 'weekly']):
            return 'week'
        elif any(word in message_lower for word in ['this month', 'month', 'monthly']):
            return 'month'
        elif any(word in message_lower for word in ['this year', 'year', 'yearly', 'annually']):
            return 'year'
        else:
            return 'month'  # Default to month
    
    async def process_message(self, user_id: str, message: str, context_data: Dict[str, Any]) -> ChatMessage:
        """Process user message and generate appropriate response"""
        
        # Classify intent
        intent, confidence = self.classify_intent(message)
        
        # Generate response based on intent
        if intent == 'greeting':
            response = self.response_templates['greeting'][0]
        elif intent == 'goodbye':
            response = self.response_templates['goodbye'][0]
        elif intent == 'help':
            response = self.response_templates['help'][0]
        elif intent == 'balance_inquiry':
            response = self.get_balance_response(context_data)
        elif intent == 'spending_inquiry':
            timeframe = self.extract_timeframe_from_message(message)
            response = self.get_spending_response(context_data, timeframe)
        elif intent == 'transaction_history':
            response = self.get_transaction_history_response(context_data)
        elif intent == 'affordability_check':
            amount = self.extract_amount_from_message(message)
            response = self.get_affordability_response(context_data, amount)
        elif intent == 'exchange_rates':
            response = self.get_exchange_rates_response(context_data)
        elif intent == 'financial_advice':
            response = self.get_financial_advice_response(context_data)
        else:
            response = "I'm not sure how to help with that. Try asking about your balance, spending, transactions, or type 'help' to see what I can do!"
        
        # Create chat message object
        chat_message = ChatMessage(
            id=str(uuid.uuid4()),
            user_id=user_id,
            message=message,
            response=response,
            timestamp=datetime.utcnow(),
            context_data=context_data,
            intent=intent,
            confidence=confidence
        )
        
        return chat_message
    
    def get_quick_actions(self) -> List[Dict[str, str]]:
        """Get quick action buttons for the chat interface"""
        return [
            {"text": "💰 Check Balance", "query": "What's my current balance?"},
            {"text": "📊 Monthly Spending", "query": "How much did I spend this month?"},
            {"text": "📋 Recent Transactions", "query": "Show me my recent transactions"},
            {"text": "💱 Exchange Rates", "query": "Show me current exchange rates"},
            {"text": "💡 Financial Advice", "query": "Give me some financial advice"},
            {"text": "❓ Help", "query": "What can you help me with?"}
        ]