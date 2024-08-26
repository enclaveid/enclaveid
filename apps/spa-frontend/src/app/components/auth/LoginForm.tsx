import { useState } from 'react';
import { Logo } from '../atoms/Logo';
import { Input } from '../atoms/Input';
import { Button } from '../atoms/Button';
import { FormCardLayout } from '../FormCardLayout';
import { useNavigate } from 'react-router-dom';

export interface LoginFormProps {
  handleSubmit?: (formData: { email: string; password: string }) => void;
}

export function LoginForm({ handleSubmit }: LoginFormProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-white p-[10%]">
      <div className="flex flex-col gap-10 max-w-[478px] w-full mx-auto">
        <Logo />
        <FormCardLayout>
          <div className="flex flex-col gap-5">
            <Input
              placeholder="yourmail@gmail.com"
              type="email"
              fullWidth
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <Input
              placeholder="**********"
              type="password"
              fullWidth
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <div className="mt-5">
            <Button
              label="Log In"
              fullWidth
              onClick={() => {
                if (handleSubmit) handleSubmit({ email, password });
              }}
            />
          </div>
          <div className="mt-5">
            <Button
              label="Sign Up for a new account"
              variant="secondary"
              fullWidth
              onClick={() => {
                navigate('/signup');
              }}
            />
          </div>
        </FormCardLayout>
      </div>
    </div>
  );
}
