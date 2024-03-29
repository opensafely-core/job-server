import { node } from "prop-types";

function InputError({ children }) {
  return (
    <div className="border-l-2 border-l-bn-ribbon-600 bg-bn-ribbon-100 max-w-prose p-2 pl-4 mt-2 text-sm font-semibold text-bn-ribbon-800">
      {children}
    </div>
  );
}

export default InputError;

InputError.propTypes = {
  children: node.isRequired,
};
