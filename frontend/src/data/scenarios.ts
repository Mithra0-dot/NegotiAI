import type { Scenario } from "../types/scenario";

/**
 * Static scenario config for the picker screen. Later this becomes a
 * `GET /scenarios` call against the backend's persona configs — kept here
 * as a plain array in the meantime so ScenarioPicker doesn't need to know
 * the difference.
 */
export const scenarios: Scenario[] = [
  {
    id: "salary-negotiation",
    name: "Salary Negotiation",
    blurb:
      "You've got a competing offer and a hiring manager who wants you to accept today.",
    difficulty: "Medium",
    opponentStyleHint: "Deadline pressure, anchors low",
  },
  {
    id: "freelance-rate",
    name: "Freelance Rate",
    blurb:
      "A repeat client loves your work but wants a 'friends and family' discount, again.",
    difficulty: "Easy",
    opponentStyleHint: "Collaborative, leans on rapport",
  },
  {
    id: "apartment-lease",
    name: "Apartment Lease",
    blurb:
      "The landlord won't budge on rent but might move on move-in date and repairs.",
    difficulty: "Medium",
    opponentStyleHint: "Rigid on price, flexible on terms",
  },
  {
    id: "cofounder-equity-split",
    name: "Cofounder Equity Split",
    blurb:
      "You and your cofounder both think you're bringing more to the table.",
    difficulty: "Hard",
    opponentStyleHint: "Data-driven, cites market comps",
  },
];
