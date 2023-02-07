function Fieldset({
  children,
  legend,
}: {
  children: React.ReactNode;
  legend: string;
}) {
  return (
    <fieldset>
      <legend className="text-2xl font-bold mb-4">
        <h2>{legend}</h2>
      </legend>
      <div className="flex flex-col gap-4">{children}</div>
    </fieldset>
  );
}

export default Fieldset;
