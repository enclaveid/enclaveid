import { useCallback, useEffect, useState, useRef } from 'react';
import { trpc } from '../utils/trpc';
import { Button } from '../components/Button';
import { ChromeUserEventEnum } from '@enclaveid/shared';

// TODO: maybe we wanna serve it from the tunnel and load it dynamically?
// https://guacamole.apache.org/doc/gug/writing-you-own-guacamole-app.html#updating-pom-xml
import Guacamole from '../utils/guacamole';

export function FakeOauthPage() {
  const startSession = trpc.private.startSession.useMutation();

  const [connecting, setConnecting] = useState(false);
  const [podId, setPodId] = useState(null);
  const [guacClient, setGuacClient] = useState<Guacamole.Client | null>(null);

  const displayRef = useRef<HTMLDivElement>(null);

  const connectGuac = useCallback((password, hostname, connectionId) => {
    setConnecting(true);

    const guacTunnel = new Guacamole.HTTPTunnel(
      import.meta.env['VITE_GUAC_TUNNEL_URL'] ||
        'http://enclaveid-guacamole-tunnel.default.svc.cluster.local/tunnel',
      true,
      {
        password,
        hostname,
        connectionId,
      },
    );

    guacTunnel.onerror = (err) => console.error('Guac tunnel error', err);
    guacTunnel.onstatechange = (state) =>
      console.log('Guac tunnel state', state);

    setGuacClient(new Guacamole.Client(guacTunnel));
  }, []);

  useEffect(() => {
    if (!guacClient) return;

    guacClient.onerror = (err) => console.error('Guac client error', err);
    guacClient.onstatechange = (state) =>
      console.log('Guac client state', state);

    const guacCanvas = guacClient.getDisplay().getElement();

    displayRef.current?.appendChild(guacCanvas);

    // Cover the Chrome banner
    // TODO: Can we do it server side?
    const cover = document.createElement('div');
    cover.style.position = 'absolute';
    cover.style.top = '0';
    cover.style.left = '0';
    cover.style.width = '100%';
    cover.style.height = '60px';
    cover.style.backgroundColor = 'white';
    cover.style.zIndex = '1000';
    guacCanvas.appendChild(cover);

    guacClient.connect();

    // Mouse
    const mouse = new Guacamole.Mouse(guacClient.getDisplay().getElement());

    mouse.onmousedown =
      mouse.onmouseup =
      mouse.onmousemove =
        (mouseState) => {
          // TODO: We should hide the mouse server side rather than here
          guacClient.getDisplay().showCursor(false);

          guacClient.sendMouseState(mouseState);
        };

    // Keyboard
    const keyboard = new Guacamole.Keyboard(document);

    keyboard.onkeydown = (keysym) => {
      guacClient.sendKeyEvent(1, keysym);
    };

    keyboard.onkeyup = (keysym) => {
      guacClient.sendKeyEvent(0, keysym);
    };
  }, [guacClient]);

  trpc.private.podEvents.useSubscription(
    { podName: podId },
    {
      enabled: !!podId,
      onData: ({ event, data }) => {
        switch (event) {
          case ChromeUserEventEnum.LOGIN_SUCCESS:
            guacClient.disconnect();
            displayRef.current?.removeChild(
              guacClient.getDisplay().getElement(),
            );
            setPodId(null);
            break;
          case ChromeUserEventEnum.NEW_BOUNDING_BOX:
            console.log('NEW_BOUNDING_BOX', data); // TODO
            break;
          case ChromeUserEventEnum.CHROME_READY:
            setConnecting(false);
            break;
        }
      },
      onError: (err) => console.error('Pod event error', err),
    },
  );

  return (
    <div>
      <Button
        label="Connect"
        onClick={() => {
          startSession
            .mutateAsync({
              isMobile: false,
              viewport: {
                vh: 1080,
                vw: 1920,
              },
            })
            .then((pod) => {
              setPodId(pod.chromePodId);
              connectGuac(pod.rdpPassword, pod.hostname, pod.chromePodId);
            });
        }}
      />
      {connecting && (
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '5px',
            zIndex: 1000,
          }}
        >
          Connecting...
        </div>
      )}
      <div
        id="display"
        ref={displayRef}
        style={{
          height: '1000px',
          width: '1000px',
          display: 'block',
          opacity: connecting ? 0 : 1,
        }}
      ></div>
    </div>
  );
}
