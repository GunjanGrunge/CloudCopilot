import React, { useState, useRef, useEffect } from 'react';
import { Container, Form, Button, Stack, Toast, Alert, Modal } from 'react-bootstrap';
import { ChatMessage } from './ChatMessage';
import { sendChatMessage, Message } from '../services/api';
import { FaPaperPlane, FaAws } from 'react-icons/fa';
import { IoCloudOutline } from 'react-icons/io5';
import 'bootstrap/dist/css/bootstrap.min.css';

interface AWSCredentials {
  accessKeyId: string;
  secretAccessKey: string;
  region: string;
}

export const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [showCredentialsModal, setShowCredentialsModal] = useState(false);
  const [awsCredentials, setAwsCredentials] = useState<AWSCredentials | null>(null);
  const [credentialsPromiseResolve, setCredentialsPromiseResolve] = useState<((value: AWSCredentials) => void) | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const requestAwsCredentials = async (): Promise<AWSCredentials> => {
    return new Promise((resolve) => {
      setCredentialsPromiseResolve(() => resolve);
      setShowCredentialsModal(true);
    });
  };

  const handleCredentialsSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const credentials: AWSCredentials = {
      accessKeyId: form.accessKeyId.value,
      secretAccessKey: form.secretAccessKey.value,
      region: form.region.value || 'ap-south-1'
    };
    setAwsCredentials(credentials);
    if (credentialsPromiseResolve) {
      credentialsPromiseResolve(credentials);
    }
    setShowCredentialsModal(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    setError(null);
    const userMessage: Message = {
      role: 'user',
      content: input,
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const requestData = {
        messages: [...messages, userMessage],
        awsCredentials
      };

      const response = await sendChatMessage(requestData);
      
      if (response.requiresCredentials && !awsCredentials) {
        const credentials = await requestAwsCredentials();
        // Retry the request with credentials
        const retryResponse = await sendChatMessage({
          ...requestData,
          awsCredentials: credentials
        });
        handleChatResponse(retryResponse);
      } else {
        handleChatResponse(response);
      }
    } catch (error) {
      handleError(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChatResponse = (response: any) => {
    const assistantMessage: Message = {
      role: 'assistant',
      content: response.response,
    };

    setMessages(prev => [...prev, assistantMessage]);

    if (response.actions_taken.length > 0) {
      setToastMessage(response.actions_taken.join('\n'));
      setShowToast(true);
    }
  };

  const handleError = (error: any) => {
    console.error('API Error:', error);
    let errorMessage = 'Failed to get response from CloudPilot';
    if (error instanceof Error) {
      errorMessage = `${errorMessage}: ${error.message}`;
    }
    setError(errorMessage);
    setToastMessage(errorMessage);
    setShowToast(true);
  };

  return (
    <Container className="py-4" style={{ height: '100vh' }}>
      <Stack gap={3} className="h-100">
        <div className="text-center py-2 d-flex align-items-center justify-content-center">
          <FaAws size={24} color="#FF9900" className="me-2" />
          <h4 className="mb-0">CloudPilot Assistant</h4>
          <IoCloudOutline size={24} color="#0080FF" className="ms-2" />
        </div>
        
        {error && (
          <Alert variant="danger" onClose={() => setError(null)} dismissible>
            {error}
          </Alert>
        )}
        
        <div className="flex-grow-1 border rounded p-3 overflow-auto bg-white">
          {messages.map((message, index) => (
            <ChatMessage key={index} message={message} />
          ))}
          <div ref={messagesEndRef} />
        </div>

        <Form onSubmit={handleSubmit} className="mt-3">
          <Stack direction="horizontal" gap={2}>
            <Form.Control
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask CloudPilot about AWS..."
              disabled={isLoading}
            />
            <Button 
              type="submit" 
              variant="primary"
              disabled={isLoading}
              className="d-flex align-items-center justify-content-center"
              style={{ width: '40px', height: '38px' }}
            >
              <FaPaperPlane size={16} />
            </Button>
          </Stack>
        </Form>
      </Stack>

      <Toast 
        show={showToast} 
        onClose={() => setShowToast(false)}
        delay={5000}
        autohide
        style={{
          position: 'fixed',
          top: 20,
          right: 20,
          minWidth: '250px'
        }}
      >
        <Toast.Header>
          <strong className="me-auto">Notification</strong>
        </Toast.Header>
        <Toast.Body>{toastMessage}</Toast.Body>
      </Toast>

      <Modal show={showCredentialsModal} onHide={() => setShowCredentialsModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>AWS Credentials Required</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form onSubmit={handleCredentialsSubmit}>
            <Form.Group className="mb-3">
              <Form.Label>Access Key ID</Form.Label>
              <Form.Control
                type="text"
                name="accessKeyId"
                placeholder="Enter AWS Access Key ID"
                required
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Secret Access Key</Form.Label>
              <Form.Control
                type="password"
                name="secretAccessKey"
                placeholder="Enter AWS Secret Access Key"
                required
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Region</Form.Label>
              <Form.Control
                type="text"
                name="region"
                placeholder="Enter AWS Region (default: ap-south-1)"
                defaultValue="ap-south-1"
              />
            </Form.Group>
            <Button variant="primary" type="submit">
              Submit
            </Button>
          </Form>
        </Modal.Body>
      </Modal>
    </Container>
  );
};