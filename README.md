# Currency Recognition AI App

A full-stack application that uses dual AI models (OpenAI GPT-4o-mini and Google Gemini 2.0 Flash) to recognize and analyze currency from uploaded images.

## Features

- 🤖 **Dual AI Analysis**: Compare results from OpenAI and Gemini Vision models
- 💰 **Currency Support**: UAH, USD, EUR recognition
- 🔐 **JWT Authentication**: Secure user registration and login
- 📱 **Real-time Analysis**: Fast image processing and results
- 🎯 **High Accuracy**: Dual model comparison for enhanced reliability
- 📊 **Analysis History**: Track previous currency recognitions

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **MongoDB**: Document database for storing analyses
- **JWT**: Secure authentication
- **emergentintegrations**: AI model integration library
- **OpenAI GPT-4o-mini**: Primary vision model
- **Google Gemini 2.0 Flash**: Secondary vision model for comparison

### Frontend
- **React 18**: Modern UI framework
- **Tailwind CSS**: Utility-first styling
- **Axios**: HTTP client for API calls

## API Endpoints

### Authentication
- `POST /api/register` - User registration
- `POST /api/login` - User login

### Currency Analysis
- `POST /api/analyze-currency` - Upload image for AI analysis
- `GET /api/analysis/{id}` - Get specific analysis result
- `GET /api/analysis` - Get user's recent analyses

### System
- `GET /api/health` - Health check
- `POST /api/webhook/{analysis_id}` - Webhook for real-time updates

## Supported Currencies

- 🇺🇦 **UAH** - Ukrainian Hryvnia
- 🇺🇸 **USD** - US Dollar
- 🇪🇺 **EUR** - Euro

## How It Works

1. **Upload**: User uploads an image of banknotes or coins
2. **Dual Analysis**: Image is analyzed by both OpenAI and Gemini models simultaneously
3. **Comparison**: Results are compared for accuracy and reliability
4. **Display**: Detailed analysis showing currency type, denomination, quantity, and confidence levels
5. **Storage**: Analysis results stored for future reference

## Response Format

```json
{
  "analysis_id": "uuid",
  "openai_result": {
    "currencies_detected": [
      {
        "currency_type": "USD",
        "denomination": "20",
        "quantity": 1,
        "confidence": "high"
      }
    ],
    "total_value": "20 USD",
    "notes": "Clear image, well-lit banknote",
    "provider": "OpenAI GPT-4o-mini"
  },
  "gemini_result": {
    "currencies_detected": [
      {
        "currency_type": "USD", 
        "denomination": "20",
        "quantity": 1,
        "confidence": "high"
      }
    ],
    "total_value": "20 USD",
    "notes": "High confidence detection",
    "provider": "Google Gemini 2.0 Flash"
  },
  "combined_analysis": {
    "comparison": "dual_ai_analysis",
    "consensus": {
      "currency_count_match": true
    },
    "discrepancies": []
  },
  "timestamp": "2025-01-XX"
}
```

## Development

The application runs on:
- Backend: http://localhost:8001
- Frontend: http://localhost:3000

## Security Features

- JWT token-based authentication
- Secure password hashing with bcrypt
- CORS protection
- Input validation and sanitization
- API rate limiting ready

## Future Enhancements

- Real-time WebSocket updates
- Support for more currencies
- Batch image processing
- Mobile app version
- Advanced analytics dashboard
