import { z } from "zod";

export const loginSchema = z.object({
  username: z.string().trim().min(1, "Ingresa tu usuario"),
  password: z.string().min(1, "Ingresa tu contrasena"),
});

export const createUserSchema = z
  .object({
    username: z.string().trim().min(3, "Minimo 3 caracteres"),
    password: z.string().min(6, "Minimo 6 caracteres"),
    confirmPassword: z.string().min(1, "Confirma la contrasena"),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Las contrasenas no coinciden",
    path: ["confirmPassword"],
  });
