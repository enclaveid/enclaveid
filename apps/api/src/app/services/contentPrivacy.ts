export function replaceUserIds(text, userIds, usernames) {
  // Create a regular expression that matches any of the user IDs (case insensitive)
  const regex = new RegExp(userIds.join('|'), 'gi');

  // Create a mapping of user IDs to usernames
  const userMap = Object.fromEntries(
    userIds.map((id, index) => [id, usernames[index]]),
  );

  // Replace all occurrences of user IDs with their corresponding usernames
  return text.replace(regex, (matched) => userMap[matched]);
}
