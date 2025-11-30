import prisma from "./prisma";

async function main() {
  await prisma.role.createMany({
    data: [
      { name: "Frontend", description: "Frontend development" },
      { name: "Backend", description: "Backend development" },
      { name: "AI", description: "AI/ML engineering" },
      { name: "ETC", description: "Other tasks" }
    ],
    skipDuplicates: true
  });
}

main()
  .then(() => console.log("Role seed completed"))
  .catch((e) => console.error(e))
  .finally(() => process.exit(0));
