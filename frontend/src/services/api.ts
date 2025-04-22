import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface AWSCredentials {
  accessKeyId: string;
  secretAccessKey: string;
  region: string;
}

export interface ChatRequest {
  messages: Message[];
  user_id?: string;
  aws_context?: Record<string, any>;
  awsCredentials?: AWSCredentials;
}

export interface ChatResponse {
  response: string;
  actions_taken: string[];
  aws_resources_affected: Array<{
    operation: string;
    service: string;
    parameters: Record<string, any>;
  }>;
  requiresCredentials?: boolean;
  error?: string;
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const sendChatMessage = async (request: ChatRequest): Promise<ChatResponse> => {
  try {
    const response = await api.post<ChatResponse>('/chat', request);
    return response.data;
  } catch (error: any) {
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail);
    }
    throw error;
  }
};

export const suggestIAMPolicy = async (description: string, credentials?: AWSCredentials) => {
  try {
    const response = await api.post('/suggest-iam-policy', { 
      description,
      awsCredentials: credentials 
    });
    return response.data;
  } catch (error: any) {
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail);
    }
    throw error;
  }
};

export const validateAWSOperation = async (operation: Record<string, any>, credentials?: AWSCredentials) => {
  try {
    const response = await api.post('/validate-aws-operation', { 
      operation,
      awsCredentials: credentials 
    });
    return response.data;
  } catch (error: any) {
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail);
    }
    throw error;
  }
};