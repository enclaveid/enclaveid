'use client';

import { cn } from '@enclaveid/ui-utils';
import { Button } from '@enclaveid/ui/button';
import { Input } from '@enclaveid/ui/input';
import { Label } from '@enclaveid/ui/label';
// import GitHubIcon from '~icons/mdi/github.tsx';
import { signIn } from 'next-auth/react';
import { Logo } from './logo';

export function LoginForm({
  className,
  ...props
}: React.ComponentPropsWithoutRef<'div'>) {
  return (
    <div className={cn('flex flex-col gap-6', className)} {...props}>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          const formData = new FormData(e.currentTarget);
          await signIn('email', {
            email: formData.get('email'),
          });
        }}
      >
        <div className="flex flex-col gap-6">
          <div className="flex flex-col items-center gap-2">
            <a
              href="#"
              className="flex flex-col items-center gap-2 font-medium"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-md">
                <Logo />
              </div>
              <span className="sr-only">EnclaveID</span>
            </a>
            <h1 className="text-xl font-bold">Welcome to EnclaveID</h1>
            <div className="text-center text-sm">Get LLMs to know you</div>
          </div>
          <div className="flex flex-col gap-6">
            <div className="grid gap-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                name="email"
                type="email"
                placeholder="john.doe@example.com"
                required
              />
            </div>
            <Button type="submit" className="w-full">
              Continue
            </Button>
          </div>
          <div className="relative text-center text-sm after:absolute after:inset-0 after:top-1/2 after:z-0 after:flex after:items-center after:border-t after:border-border">
            <span className="relative z-10 bg-background px-2 text-muted-foreground">
              Or
            </span>
          </div>
          <Button
            type="button"
            variant="outline"
            className="w-full"
            onClick={() => signIn('github')}
          >
            {/* <GitHubIcon className="w-6 h-6" /> */}
            Continue with GitHub
          </Button>
        </div>
      </form>
      <div className="text-balance text-center text-xs text-muted-foreground [&_a]:underline [&_a]:underline-offset-4 hover:[&_a]:text-primary  ">
        By clicking continue, you agree to our <a href="#">Terms of Service</a>{' '}
        and <a href="#">Privacy Policy</a>.
      </div>
    </div>
  );
}
