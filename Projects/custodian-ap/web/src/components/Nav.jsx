// Section navigation. Collapses to a horizontal scroller under 820px (see
// .sidenav in styles.css), so it works as a sidebar on desktop and a tab strip
// on mobile without a second component.

export default function Nav({ views, active, onNavigate, badges = {} }) {
  return (
    <nav className="sidenav" aria-label="Sections">
      {views.map((view) => {
        const isActive = view.id === active
        const badge = badges[view.id]
        return (
          <button
            key={view.id}
            type="button"
            className={`navitem${isActive ? ' active' : ''}`}
            // aria-current is what tells a screen reader which section is open;
            // the active styling alone carries no semantics.
            aria-current={isActive ? 'page' : undefined}
            onClick={() => onNavigate(view.id)}
          >
            <span className="navicon" aria-hidden="true">{view.icon}</span>
            <span className="navlabel">{view.label}</span>
            {badge ? (
              <span className="navbadge" aria-label={`${badge} awaiting review`}>{badge}</span>
            ) : null}
          </button>
        )
      })}
    </nav>
  )
}
