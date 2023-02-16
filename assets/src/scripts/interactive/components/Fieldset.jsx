import { node, string } from "prop-types";

function Fieldset({ children, legend }) {
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

Fieldset.propTypes = {
  children: node.isRequired,
  legend: string.isRequired,
};
