import { generate } from 'random-words';

export function getPressureMessage() {
  const templates = [
    //'Your clicks have caused a {noun1} overflow in our {noun2} database.',
    'Ok, we will replace all the variable names with "{noun1}" and function names with "{noun2}".',
    'Understood. The team will now prioritize this feature over implementing a real-time {noun1}-{noun2} detector.',
    'The CEO has been notified of the situation and has promised to provide the dev team with more {noun1}able {noun2}s.',
    "We'll implement this feature as soon as the EKS team implements ISO timestamps as they said they would.",
  ];

  const template = templates[Math.floor(Math.random() * templates.length)];
  return template.replace(/{noun\d}/g, function () {
    return generate({ exactly: 1, minLength: 8 })[0];
  });
}
