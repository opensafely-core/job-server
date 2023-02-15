import { element } from "prop-types";

function HintText({ children }) {
  return (
    <div className="-mt-2 mb-0.5 text-sm text-gray-700 flex flex-col gap-y-1">
      {children}
    </div>
  );
}

export default HintText;

HintText.propTypes = {
  children: element.isRequired,
};
