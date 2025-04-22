import { Card, Stack } from 'react-bootstrap';
import { Message } from '../services/api';
import { FaRobot, FaUser, FaAws } from 'react-icons/fa';

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isAssistant = message.role === 'assistant';
  
  return (
    <Card 
      className={`my-2 ${isAssistant ? 'bg-light' : 'bg-white'}`}
      style={{ maxWidth: '100%' }}
    >
      <Card.Body>
        <Stack gap={2}>
          <div className="d-flex align-items-center">
            {isAssistant ? (
              <>
                <FaRobot className="text-primary me-2" />
                <FaAws style={{ color: '#FF9900' }} className="me-2" />
                <span className="fw-bold text-primary">CloudPilot</span>
              </>
            ) : (
              <>
                <FaUser className="text-secondary me-2" />
                <span className="fw-bold text-secondary">You</span>
              </>
            )}
          </div>
          {message.content.includes('```') ? (
            message.content.split('```').map((part, index) => (
              index % 2 === 1 ? (
                <pre key={index} className="bg-dark text-light p-2 rounded">
                  <code>{part}</code>
                </pre>
              ) : (
                <div key={index} style={{ whiteSpace: 'pre-wrap' }}>
                  {part}
                </div>
              )
            ))
          ) : (
            <div style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>
          )}
        </Stack>
      </Card.Body>
    </Card>
  );
};