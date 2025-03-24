import { assertEquals } from "std/assert/mod.ts";
import { SlackFunctionTester } from "deno-slack-sdk/mod.ts";
import handler from "./extract_github_username.ts";

// Initialize the function tester
const { createContext } = SlackFunctionTester("extract_github_username_function");

// Test case 1: Extract username using pattern "GitHub: username"
Deno.test("Extract username from 'GitHub: username' pattern", async () => {
  const inputs = {
    message_text: "Please add this person to our GitHub: testuser1"
  };
  
  const { outputs } = await handler(createContext({ inputs }));
  
  assertEquals(outputs?.github_username, "testuser1");
});

// Test case 2: Extract username using pattern "GitHub username: username"
Deno.test("Extract username from 'GitHub username: username' pattern", async () => {
  const inputs = {
    message_text: "GitHub username: testuser2"
  };
  
  const { outputs } = await handler(createContext({ inputs }));
  
  assertEquals(outputs?.github_username, "testuser2");
});

// Test case 3: Extract username using pattern "@username on GitHub"
Deno.test("Extract username from '@username on GitHub' pattern", async () => {
  const inputs = {
    message_text: "We need to add @testuser3 on GitHub"
  };
  
  const { outputs } = await handler(createContext({ inputs }));
  
  assertEquals(outputs?.github_username, "testuser3");
});

// Test case 4: Extract username using pattern "github.com/username"
Deno.test("Extract username from 'github.com/username' pattern", async () => {
  const inputs = {
    message_text: "Profile: github.com/testuser4"
  };
  
  const { outputs } = await handler(createContext({ inputs }));
  
  assertEquals(outputs?.github_username, "testuser4");
});

// Test case 5: Extract username with @ prefix
Deno.test("Extract username with @ prefix", async () => {
  const inputs = {
    message_text: "GitHub: @testuser5"
  };
  
  const { outputs } = await handler(createContext({ inputs }));
  
  assertEquals(outputs?.github_username, "testuser5");
});

// Test case 6: Extract username from fallback method
Deno.test("Extract username from fallback method", async () => {
  const inputs = {
    message_text: "Please add testuser6 to our organization"
  };
  
  const { outputs } = await handler(createContext({ inputs }));
  
  assertEquals(outputs?.github_username, "testuser6");
});

// Test case 7: Handle no username in text
Deno.test("Handle no username in text", async () => {
  const inputs = {
    message_text: "This message has no GitHub username"
  };
  
  const { outputs } = await handler(createContext({ inputs }));
  
  assertEquals(outputs?.github_username, "");
});

// Test case 8: Extract username with hyphens and underscores
Deno.test("Extract username with hyphens and underscores", async () => {
  const inputs = {
    message_text: "GitHub: test-user_8"
  };
  
  const { outputs } = await handler(createContext({ inputs }));
  
  assertEquals(outputs?.github_username, "test-user_8");
}); 