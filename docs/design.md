# Kisan Mitra — Product and UX Design

## 1. Design Goal

The interface is designed around one principle:

> A farmer should be able to ask a practical crop question without needing to understand AI technology.

The UI therefore prioritizes a short interaction flow, readable responses, and visible trust signals.

## 2. Interface Structure

### Header

- Kisan Mitra branding
- Short description explaining the purpose of the application

### Query Section

The user can provide:

- Natural-language question
- Crop selection
- Response language
- District
- Weather toggle

### Result Section

The result page presents:

1. Advisory
2. Step-by-step guidance where appropriate
3. Weather context where relevant
4. Source identifier
5. Safety/AI disclaimer
6. Additional details

## 3. UX Principles

### Simplicity

Avoid exposing technical concepts such as embeddings, vector distances, or prompt engineering to the farmer unless useful.

### Trust

Show the source used by the RAG system.

### Transparency

Make it clear that the response is AI-generated and that critical decisions should be verified with local agricultural experts.

### Accessibility

Use straightforward language, short paragraphs, numbered instructions, and familiar terminology.

### Multilingual Design

Allow users to interact in English, Hindi, Punjabi, and Hinglish.

## 4. Visual Language

The current interface uses:

- Dark visual theme
- High-contrast text
- Green agricultural branding
- Clear action button
- Card-based input and result sections
- Status indicator for successful advisory generation

The visual identity uses agricultural imagery and the name **Kisan Mitra** to make the application immediately understandable.

## 5. Response Design

A good response should generally follow:

```text
Direct recommendation
        ↓
Step-by-step guidance
        ↓
Weather/context note
        ↓
Safety warning
        ↓
Source
        ↓
AI/KVK disclaimer
```

Not every query requires every section; the response should remain proportional to the question.

## 6. Error and Uncertainty Design

When evidence is insufficient, the system should prefer:

> "I don't have enough PAU data in the provided context..."

rather than inventing an answer.

This behavior is intentional and is part of the product's trust model.

## 7. Future UX Improvements

- Voice input/output
- Larger accessibility controls
- Offline/low-connectivity support
- Farm profile
- Crop calendar visualization
- Weather timeline
- Image upload for crop/disease analysis
- Personalized recommendations
