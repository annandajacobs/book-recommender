export function SystemBubble({ label = "Estante", children }) {
  return (
    <div className="msg system">
      <span className="msg-avatar" aria-hidden="true">
        E
      </span>
      <div className="msg-body">
        <div className="msg-label">{label}</div>
        <div className="msg-bubble">{children}</div>
      </div>
    </div>
  );
}

export function UserBubble({ children }) {
  return (
    <div className="msg user">
      <div className="msg-body">
        <div className="msg-bubble">{children}</div>
      </div>
      <span className="msg-avatar user" aria-hidden="true">
        Você
      </span>
    </div>
  );
}

// Rich/structured content (book list, forms) — rendered under the system
// avatar without a second layer of bubble chrome, so cards keep their own
// styling instead of a box-inside-a-box.
export function SystemContent({ label, children }) {
  return (
    <div className="msg system">
      <span className="msg-avatar" aria-hidden="true">
        E
      </span>
      <div className="msg-body msg-body-wide">
        {label && <div className="msg-label">{label}</div>}
        {children}
      </div>
    </div>
  );
}

export function TypingBubble({ label = "Pensando…" }) {
  return (
    <div className="msg system">
      <span className="msg-avatar" aria-hidden="true">
        E
      </span>
      <div className="msg-body">
        <div className="msg-bubble typing-bubble">
          <span className="typing-dots" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
          <span className="typing-label">{label}</span>
        </div>
      </div>
    </div>
  );
}
