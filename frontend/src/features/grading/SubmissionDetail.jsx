function toLinks(submission) {
  const links = submission?.links;
  if (!Array.isArray(links)) {
    return [];
  }
  return links.filter((link) => typeof link === "string" && link.trim() !== "");
}

export default function SubmissionDetail({ submission }) {
  const content = submission?.content?.trim() ?? "";
  const links = toLinks(submission);

  return (
    <div data-testid="submission-detail">
      <h6 className="text-uppercase small text-secondary">Texto</h6>
      {content ? (
        <div className="campus-submission-text" data-testid="submission-detail-content">
          {content}
        </div>
      ) : (
        <p className="text-secondary fst-italic mb-0" data-testid="submission-detail-content">
          Sin texto.
        </p>
      )}

      <h6 className="text-uppercase small text-secondary mt-4">Enlaces</h6>
      {links.length > 0 ? (
        <ul
          className="list-unstyled d-flex flex-column gap-2 mb-0"
          data-testid="submission-detail-links"
        >
          {links.map((link, index) => (
            <li key={`${index}-${link}`}>
              <a
                href={link}
                target="_blank"
                rel="noopener noreferrer"
                className="text-break d-inline-flex align-items-start gap-1"
              >
                <i className="bi bi-box-arrow-up-right mt-1" aria-hidden="true" />
                <span>{link}</span>
              </a>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-secondary fst-italic mb-0" data-testid="submission-detail-links">
          Sin enlaces.
        </p>
      )}
    </div>
  );
}
