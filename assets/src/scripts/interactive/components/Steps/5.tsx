function Step5() {
  const uuid = crypto.randomUUID().split("-").slice(0, 1)[0];

  return (
    <div className="prose prose-lg mb-10">
      <h1>Your request is being processed</h1>
      <p>
        Your reference number:{` `}
        <span className="font-bold font-mono">{uuid}</span>
      </p>
      <p>We will notify you when your analysis is ready.</p>
      <p>
        The results will be checked carefully by our team for privacy and
        security reasons. We aim to process requests within two working days.
      </p>
    </div>
  );
}

export default Step5;
