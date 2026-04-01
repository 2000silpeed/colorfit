import BottomTabBar from "@/components/BottomTabBar";

export default function MainLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <>
      {children}
      <BottomTabBar />
    </>
  );
}
