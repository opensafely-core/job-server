import { node, string } from "prop-types";
import { useLocation } from "wouter";

function ReviewLineItem({ title, children, page }) {
  const [, navigate] = useLocation();

  return (
    <div className="py-4 sm:grid sm:grid-cols-3 sm:gap-4 sm:py-5">
      <dt className="text-lg font-bold text-gray-700 md:text-base">{title}</dt>
      <dd className="mt-1 flex text-gray-900 sm:col-span-2 sm:mt-0">
        <span className="flex-grow break-words">{children}</span>
        <span className="ml-4 flex-shrink-0">
          <button
            className="rounded-md bg-white font-medium text-oxford-600 hover:text-oxford-500 focus:outline-none focus:ring-2 focus:ring-oxford-500 focus:ring-offset-2"
            onClick={() => navigate(page)}
            type="button"
          >
            Edit
          </button>
        </span>
      </dd>
    </div>
  );
}

export default ReviewLineItem;

ReviewLineItem.propTypes = {
  title: string.isRequired,
  children: node.isRequired,
  page: string.isRequired,
};
