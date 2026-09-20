# Kisan Mitra — Product Requirements Document

## 1. Product Overview

**Kisan Mitra** is an AI-powered crop advisory application designed to make practical agricultural information easier to access for farmers, with an initial focus on Punjab.

The product combines Retrieval-Augmented Generation (RAG), a structured agricultural knowledge base, ChromaDB semantic retrieval, Google Gemini, and Open-Meteo weather data to produce conversational crop guidance.

## 2. Problem

Farmers may need quick answers about crop management, fertilizer timing, irrigation, disease symptoms, and weather-sensitive decisions. Agricultural information is often distributed across technical documents and may be difficult to search using natural language.

Kisan Mitra addresses this information-access problem through a conversational interface that retrieves relevant domain knowledge before generating an answer.

## 3. Target Users

- Small and medium farmers in Punjab
- Farmers growing paddy and wheat
- Agricultural students and educators
- Agricultural extension and advisory users
- Anyone seeking accessible crop-management information

## 4. Product Goals

1. Provide natural-language access to agricultural knowledge.
2. Ground AI responses in a curated agricultural knowledge base.
3. Support English, Hindi, Punjabi, and Hinglish queries.
4. Incorporate weather information when relevant.
5. Clearly expose the source used for an advisory.
6. Avoid unsupported recommendations when the retrieved evidence is insufficient.
7. Provide a simple web interface accessible from a browser.

## 5. Core User Journey

1. User opens Kisan Mitra.
2. User enters a crop-related question.
3. User optionally selects crop, language, and district.
4. The system expands/processes the query.
5. ChromaDB retrieves relevant knowledge.
6. Weather information is retrieved when enabled and relevant.
7. Gemini receives the retrieved context and generates the response.
8. The application displays the advisory, source, and safety guidance.

## 6. Functional Requirements

### FR-01: Natural-language queries
The user must be able to enter agricultural questions in natural language.

### FR-02: Crop context
The system should support paddy and wheat context and allow automatic crop detection where possible.

### FR-03: Multilingual interaction
The interface should support English, Hindi, Punjabi, and Hinglish queries/responses.

### FR-04: Knowledge retrieval
Relevant agricultural context must be retrieved from the vector knowledge base before generation.

### FR-05: Weather awareness
The system should retrieve weather information for the selected district when weather-aware recommendations are enabled.

### FR-06: Grounded generation
The LLM should be instructed to prioritize retrieved evidence and avoid fabricating unsupported agricultural facts.

### FR-07: Transparency
The application should show the source associated with the retrieved advisory.

### FR-08: Safety
The system should communicate that AI-generated advice does not replace qualified local agricultural guidance for critical decisions.

## 7. Non-Functional Requirements

- Simple browser-based UX
- Cloud deployable
- Reasonable startup time
- Clear failure messages
- Secret/API-key isolation through Streamlit Secrets
- Reproducible dependency installation
- Maintainable modular Python code

## 8. Success Criteria

A successful prototype should:

- Accept a real farmer-style query.
- Retrieve relevant knowledge.
- Produce a coherent grounded advisory.
- Display the source.
- Use weather context when appropriate.
- Handle unsupported questions conservatively.
- Run successfully on Streamlit Community Cloud.

## 9. Current Scope

### Included

- Paddy and wheat advisory
- RAG pipeline
- ChromaDB retrieval
- Gemini generation
- Open-Meteo weather integration
- English/Hindi/Punjabi/Hinglish interaction
- Streamlit deployment

### Future Scope

- More crops
- More districts and localized agronomy
- Soil and farm-profile inputs
- Image-based disease identification
- Voice interface
- Mobile application
- Agricultural expert feedback loop
- More extensive evaluation datasets
